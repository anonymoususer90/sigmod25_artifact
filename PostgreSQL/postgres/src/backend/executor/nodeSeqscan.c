/*-------------------------------------------------------------------------
 *
 * nodeSeqscan.c
 *	  Support routines for sequential scans of relations.
 *
 * Portions Copyright (c) 1996-2022, PostgreSQL Global Development Group
 * Portions Copyright (c) 1994, Regents of the University of California
 *
 *
 * IDENTIFICATION
 *	  src/backend/executor/nodeSeqscan.c
 *
 *-------------------------------------------------------------------------
 */
/*
 * INTERFACE ROUTINES
 *		ExecSeqScan				sequentially scans a relation.
 *		ExecSeqNext				retrieve next tuple in sequential order.
 *		ExecInitSeqScan			creates and initializes a seqscan node.
 *		ExecEndSeqScan			releases any storage allocated.
 *		ExecReScanSeqScan		rescans the relation
 *
 *		ExecSeqScanEstimate		estimates DSM space needed for parallel scan
 *		ExecSeqScanInitializeDSM initialize DSM for parallel scan
 *		ExecSeqScanReInitializeDSM reinitialize DSM for fresh parallel scan
 *		ExecSeqScanInitializeWorker attach to DSM info in parallel worker
 */
#include "postgres.h"

#include "access/relscan.h"
#include "access/tableam.h"
#include "executor/execdebug.h"
#include "executor/nodeSeqscan.h"
#include "utils/rel.h"
#include "miscadmin.h"

#ifdef DIVA
#include "access/heapam.h"
#include "access/ebiam.h"
#include "storage/ebi_tree.h"
#endif /* DIVA */

#ifdef LOCATOR
#include "locator/locator_executor.h"
#endif /* LOCATOR */

#ifdef IO_AMOUNT
#include "storage/bufmgr.h"
#endif /* IO_AMOUNT */

static TupleTableSlot *SeqNext(SeqScanState *node);

/* ----------------------------------------------------------------
 *						Scan Support
 * ----------------------------------------------------------------
 */

/* ----------------------------------------------------------------
 *		SeqNext
 *
 *		This is a workhorse for ExecSeqScan
 * ----------------------------------------------------------------
 */
static TupleTableSlot *
SeqNext(SeqScanState *node)
{
	TableScanDesc scandesc;
	EState	   *estate;
	ScanDirection direction;
	TupleTableSlot *slot;

	/*
	 * get information from the estate and scan state
	 */
	scandesc = node->ss.ss_currentScanDesc;
	estate = node->ss.ps.state;
	direction = estate->es_direction;
	slot = node->ss.ss_ScanTupleSlot;

	if (scandesc == NULL)
	{
		/*
		 * We reach here if the scan is not parallel, or if we're serially
		 * executing a scan that was planned to be parallel.
		 */
#ifdef LOCATOR
#ifdef IO_AMOUNT
		List *locator_required_attidx_list =
			locator_get_required_attidx_list((ScanState *)node);
		node->ss.ss_currentRelation->locator_required_attidx_list =
			locator_required_attidx_list;
#endif /* IO_AMOUNT */
		scandesc = table_beginscan(node->ss.ss_currentRelation,
								   estate->es_snapshot,
								   0, NULL,
								   node->ss.ps.plan->hap_partid_list);
#else /* !LOCATOR */
		scandesc = table_beginscan(node->ss.ss_currentRelation,
								   estate->es_snapshot,
								   0, NULL);
#endif /* LOCATOR */
		node->ss.ss_currentScanDesc = scandesc;

#ifdef DIVA
		scandesc->siro = IsSiro(node->ss.ss_currentRelation);

		if (scandesc->siro)
			scandesc->is_heapscan = true;
#endif /* DIVA */
#ifdef LOCATOR
#ifdef IO_AMOUNT
		locator_init_columnar_slot(slot,
						node->ss.ss_currentRelation,
						locator_required_attidx_list);
#else /* !IO_AMOUNT */
		locator_init_columnar_slot(slot,
						node->ss.ss_currentRelation,
						locator_get_required_attidx_list((ScanState *)node));
#endif /* IO_AMOUNT */
#endif /* LOCATOR */
#ifdef EXECSTAMP
		fprintf(stderr, "ExecStamp: SeqScan, rel: %u, pid: %d\n",
				node->ss.ss_currentRelation->rd_id, MyProcPid);
#endif /* EXECSTAMP */
	}

#ifdef DIVA
	if (scandesc->siro)
	{
		if (scandesc->is_heapscan) {
			/* Get the next tuple from the table */
			if (table_scan_getnextslot(scandesc, direction, slot))
			{
				return slot;
			}
			
			scandesc->is_heapscan = false;
		}
		
		/* Get the next tuple from the ebi page */
		if (table_scan_getnextslot_from_ebi(scandesc, direction, slot))
		{
			return slot;
		}

#if 0
		if (scandesc->counter_in_heap + scandesc->counter_in_ebi > 10000)
			elog(LOG, 
		 		"[RESULT] rel_id: %u, # in heap: %lu, # in ebi: %lu, sum: %lu", 
		 		scandesc->rs_rd->rd_id,
		 		scandesc->counter_in_heap,
		 		scandesc->counter_in_ebi,
		 		scandesc->counter_in_heap + scandesc->counter_in_ebi);
#endif
	}
	else
	{
		if (table_scan_getnextslot(scandesc, direction, slot))
			return slot;
	}

#else
	if (table_scan_getnextslot(scandesc, direction, slot))
		return slot;
#endif /* DIVA */

	return NULL;
}

/*
 * SeqRecheck -- access method routine to recheck a tuple in EvalPlanQual
 */
static bool
SeqRecheck(SeqScanState *node, TupleTableSlot *slot)
{
	/*
	 * Note that unlike IndexScan, SeqScan never use keys in heap_beginscan
	 * (and this is very bad) - so, here we do not check are keys ok or not.
	 */
	return true;
}

/* ----------------------------------------------------------------
 *		ExecSeqScan(node)
 *
 *		Scans the relation sequentially and returns the next qualifying
 *		tuple.
 *		We call the ExecScan() routine and pass it the appropriate
 *		access method functions.
 * ----------------------------------------------------------------
 */
static TupleTableSlot *
ExecSeqScan(PlanState *pstate)
{
	SeqScanState *node = castNode(SeqScanState, pstate);

	return ExecScan(&node->ss,
					(ExecScanAccessMtd) SeqNext,
					(ExecScanRecheckMtd) SeqRecheck);
}

/* ----------------------------------------------------------------
 *		ExecInitSeqScan
 * ----------------------------------------------------------------
 */
SeqScanState *
ExecInitSeqScan(SeqScan *node, EState *estate, int eflags)
{
	SeqScanState *scanstate;

	/*
	 * Once upon a time it was possible to have an outerPlan of a SeqScan, but
	 * not any more.
	 */
	Assert(outerPlan(node) == NULL);
	Assert(innerPlan(node) == NULL);

	/*
	 * create state structure
	 */
	scanstate = makeNode(SeqScanState);
	scanstate->ss.ps.plan = (Plan *) node;
	scanstate->ss.ps.state = estate;
	scanstate->ss.ps.ExecProcNode = ExecSeqScan;

	/*
	 * Miscellaneous initialization
	 *
	 * create expression context for node
	 */
	ExecAssignExprContext(estate, &scanstate->ss.ps);

	/*
	 * open the scan relation
	 */
	scanstate->ss.ss_currentRelation =
		ExecOpenScanRelation(estate,
							 node->scan.scanrelid,
							 eflags);

	/* and create slot with the appropriate rowtype */
	ExecInitScanTupleSlot(estate, &scanstate->ss,
						  RelationGetDescr(scanstate->ss.ss_currentRelation),
						  table_slot_callbacks(scanstate->ss.ss_currentRelation));

	/*
	 * Initialize result type and projection.
	 */
	ExecInitResultTypeTL(&scanstate->ss.ps);
	ExecAssignScanProjectionInfo(&scanstate->ss);

	/*
	 * initialize child expressions
	 */
	scanstate->ss.ps.qual =
		ExecInitQual(node->scan.plan.qual, (PlanState *) scanstate);

	return scanstate;
}

/* ----------------------------------------------------------------
 *		ExecEndSeqScan
 *
 *		frees any storage allocated through C routines.
 * ----------------------------------------------------------------
 */
void
ExecEndSeqScan(SeqScanState *node)
{
	TableScanDesc scanDesc;

	/*
	 * get information from node
	 */
	scanDesc = node->ss.ss_currentScanDesc;

	/*
	 * Free the exprcontext
	 */
	ExecFreeExprContext(&node->ss.ps);

	/*
	 * clean out the tuple table
	 */
	if (node->ss.ps.ps_ResultTupleSlot)
		ExecClearTuple(node->ss.ps.ps_ResultTupleSlot);
	ExecClearTuple(node->ss.ss_ScanTupleSlot);

	/*
	 * close heap scan
	 */
	if (scanDesc != NULL)
		table_endscan(scanDesc);
}

/* ----------------------------------------------------------------
 *						Join Support
 * ----------------------------------------------------------------
 */

/* ----------------------------------------------------------------
 *		ExecReScanSeqScan
 *
 *		Rescans the relation.
 * ----------------------------------------------------------------
 */
void
ExecReScanSeqScan(SeqScanState *node)
{
	TableScanDesc scan;

	scan = node->ss.ss_currentScanDesc;

	if (scan != NULL)
		table_rescan(scan,		/* scan desc */
					 NULL);		/* new scan keys */

	ExecScanReScan((ScanState *) node);
}

/* ----------------------------------------------------------------
 *						Parallel Scan Support
 * ----------------------------------------------------------------
 */

/* ----------------------------------------------------------------
 *		ExecSeqScanEstimate
 *
 *		Compute the amount of space we'll need in the parallel
 *		query DSM, and inform pcxt->estimator about our needs.
 * ----------------------------------------------------------------
 */
void
ExecSeqScanEstimate(SeqScanState *node,
					ParallelContext *pcxt)
{
	EState	   *estate = node->ss.ps.state;

	node->pscan_len = table_parallelscan_estimate(node->ss.ss_currentRelation,
												  estate->es_snapshot);
	shm_toc_estimate_chunk(&pcxt->estimator, node->pscan_len);
	shm_toc_estimate_keys(&pcxt->estimator, 1);
}

/* ----------------------------------------------------------------
 *		ExecSeqScanInitializeDSM
 *
 *		Set up a parallel heap scan descriptor.
 * ----------------------------------------------------------------
 */
void
ExecSeqScanInitializeDSM(SeqScanState *node,
						 ParallelContext *pcxt)
{
	EState	   *estate = node->ss.ps.state;
	ParallelTableScanDesc pscan;

	pscan = shm_toc_allocate(pcxt->toc, node->pscan_len);
	table_parallelscan_initialize(node->ss.ss_currentRelation,
								  pscan,
								  estate->es_snapshot);
	shm_toc_insert(pcxt->toc, node->ss.ps.plan->plan_node_id, pscan);
#ifdef LOCATOR
	node->ss.ss_currentScanDesc =
		table_beginscan_parallel(node->ss.ss_currentRelation, pscan,
								 node->ss.ps.plan->hap_partid_list);
#else /* !LOCATOR */
	node->ss.ss_currentScanDesc =
		table_beginscan_parallel(node->ss.ss_currentRelation, pscan);
#endif /* LOCATOR */
}

/* ----------------------------------------------------------------
 *		ExecSeqScanReInitializeDSM
 *
 *		Reset shared state before beginning a fresh scan.
 * ----------------------------------------------------------------
 */
void
ExecSeqScanReInitializeDSM(SeqScanState *node,
						   ParallelContext *pcxt)
{
	ParallelTableScanDesc pscan;

	pscan = node->ss.ss_currentScanDesc->rs_parallel;
	table_parallelscan_reinitialize(node->ss.ss_currentRelation, pscan);
}

/* ----------------------------------------------------------------
 *		ExecSeqScanInitializeWorker
 *
 *		Copy relevant information from TOC into planstate.
 * ----------------------------------------------------------------
 */
void
ExecSeqScanInitializeWorker(SeqScanState *node,
							ParallelWorkerContext *pwcxt)
{
	ParallelTableScanDesc pscan;

	pscan = shm_toc_lookup(pwcxt->toc, node->ss.ps.plan->plan_node_id, false);
#ifdef LOCATOR
	node->ss.ss_currentScanDesc =
		table_beginscan_parallel(node->ss.ss_currentRelation, pscan,
								 node->ss.ps.plan->hap_partid_list);
#else /* !LOCATOR */
	node->ss.ss_currentScanDesc =
		table_beginscan_parallel(node->ss.ss_currentRelation, pscan);
#endif /* LOCATOR */
}
