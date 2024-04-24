import sys, subprocess, signal
import time, threading
from pytz import timezone
import os, random
import argparse
import pathlib, datetime
import psycopg2

CH_BASE=""

def compile_database(params=None):
	print("Compile database start ! (option:%s)"%(params))
	subprocess.run(args=DB_INSTALL_SCRIPT+"/install.sh" + params, 
		stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
		check=True, shell=True)
	print("Compile database finish !")

def init_server(params=None):
	print("Init server start !")
	subprocess.run(args=DB_SERVER_SCRIPT+"/init_server.sh" + params,
		check=True, shell=True)
	print("Init server finish !")

def run_server(params=None):
	print("Run server start")
	run_arg = DB_SERVER_SCRIPT+"/run_server.sh"
	subprocess.run(args=run_arg + params, 
		stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
		check=True, shell=True)
	time.sleep(2)
	print("Run server finish")

def shutdown_server(params=None):
	print("Shutdown server start")
	subprocess.run(args=DB_SERVER_SCRIPT+"/shutdown_server.sh" + params,
		stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
		check=True, shell=True)
	print("Shutdown server finish")

def build_dataset(args):
	global CH_BASE, DB_BASE, DB_DATA, DB_CONFIG, DB_SCRIPT, DB_SERVER_SCRIPT, DB_CLIENT_SCRIPT, DB_INSTALL_SCRIPT

	compile_options = [" ", " -DDIVA ", " -DDIVA -DLOCATOR ",  " -DDIVA -DLOCATOR "]
	modes = ["VANILLA", "DIVA", "LOCATOR_H", "LOCATOR_F"]

	LOCATOR_BASE=args.locator_path

	CH_BASE="%s/chbenchmark"%(LOCATOR_BASE)
	DB_BASE="%s/PostgreSQL"%(LOCATOR_BASE)

	DB_DATA="%s/data_current"%(args.data_path)
	DB_CONFIG=DB_BASE + "/config"

	DB_SCRIPT=DB_BASE + "/script"
	DB_SERVER_SCRIPT=DB_SCRIPT + "/script_server"
	DB_CLIENT_SCRIPT=DB_SCRIPT + "/script_client"
	DB_INSTALL_SCRIPT=DB_SCRIPT + "/script_install"
 
	if args.coredump:
		run_args = "-c"
	else:
		run_args = ""

	prev_m = -1

	print("PostgreSQL building dataset start")

	for m in range(len(modes)):
		if args.systems[m] == '0':
			continue

		print("mode: %s"%(modes[m]))

		# Compile the new system
		if prev_m < 2:
			compile_database(params=(compile_options[m] + args.compile_option))
			print("sleep 5 seconds...")
			time.sleep(5)

		prev_m = m

		init_server(params=" -d=%s"%(args.data_path))

		print("sleep 5 seconds...")
		time.sleep(5)

		# Set the config for this system
		os.system("rm %s/postgresql.conf"%(DB_DATA))
		os.system("cp %s/postgresql_%s.conf %s/postgresql.conf"%(DB_CONFIG, modes[m], DB_DATA))

		run_server(params=" -d=%s "%(args.data_path)+run_args)

		# Set the environment
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "postgres", "-c", "CREATE DATABASE locator;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "CREATE ACCESS METHOD hap TYPE TABLE HANDLER locator_hap_handler;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "CREATE ACCESS METHOD locator TYPE TABLE HANDLER locatoram_handler;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "CREATE EXTENSION intarray;"])

		print("sleep 5 seconds...")
		time.sleep(5)

		if m < 2:
			is_locator = "false"
		else:
			is_locator = "true"

		if m < 3:
			is_columnar = "false"
		else:
			is_columnar = "true"

		# Build the dataset
		os.system("%s/build.sh 4.3 %s true true %s %d %d %s"%(CH_BASE, is_locator, is_columnar, args.warehouse, args.worker, LOCATOR_BASE))

		if m > 1:
			# Wait for the partitioning worker to finish
			print("sleep 5 minutes...")
			time.sleep(300)
		else:
			print("sleep 10 seconds...")
			time.sleep(10)

		# VACUUM
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE region;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE nation;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE supplier;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE district;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE history;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE warehouse;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE new_order;"])
		subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE item;"])

		if m < 2:
			subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE customer;"])
			subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE stock;"])
			subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE orders;"])
			subprocess.call(["%s/pgsql/bin/psql"%(DB_BASE), "-h", args.pgsql_host, "-p", "5555", "-d", "locator", "-c", "VACUUM ANALYZE order_line;"])
		else:
			db = psycopg2.connect(
				host=args.pgsql_host,
				dbname=args.pgsql_db,
				port=5555
			)
			cursor = db.cursor()

			# Disable prefetching(io_uring) for setting hint bits
			cursor.execute("set enable_prefetch=off;")

			# LOCATOR does not support VACUUM, so simply set hint bits
			cursor.execute("select count(*) from customer;")
			cursor.fetchall()
			print("customer was scanned")
			cursor.execute("select count(*) from stock;")
			cursor.fetchall()
			print("stock was scanned")
			cursor.execute("select count(*) from orders;")
			cursor.fetchall()
			print("orders was scanned")
			cursor.execute("select count(*) from order_line;")
			cursor.fetchall()
			print("order_line was scanned")

			db.close()

		print("sleep 10 seconds...")
		time.sleep(10)

		shutdown_server(params=" -d=%s"%(args.data_path))

		# Restart the server to transform remained partitions
		if m > 1:
			print("sleep 5 seconds...")
			time.sleep(5)

			run_server(params=" -d=%s "%(args.data_path)+run_args)

			print("sleep 10 seconds...")
			time.sleep(10)

			shutdown_server(params=" -d=%s"%(args.data_path))

		os.system("mv %s/data_current %s/data_%d_%s"%(args.data_path, args.data_path, args.warehouse, modes[m]))


	print("building dataset done")


if __name__ == "__main__":
	# Parser
	parser = argparse.ArgumentParser(description="Sysbench Arguments...")

	pgsql_parser = parser.add_argument_group('pgsql', 'postgresql options')
	options_parser = parser.add_argument_group('options', 'other options')

	options_parser.add_argument("--compile_option", default="", help="compile options")
	options_parser.add_argument("--systems", default="1111", help="vanilla, diva, locator H, locator F")
	options_parser.add_argument("--coredump", action='store_true', default=False, help="coredump")
	options_parser.add_argument("--warehouse", type=int, default="500", help="warehouse")
	options_parser.add_argument("--worker", type=int, default="125", help="warehouse")
	options_parser.add_argument("--locator_path", default="~/sigmod25_artifact", help="locator path")
	options_parser.add_argument("--data_path", default="~/sigmod25_artifact/PostgreSQL/data", help="locator path")

	pgsql_parser.add_argument("--pgsql-host", default="localhost", help="pgsql host")
	pgsql_parser.add_argument("--pgsql-db", default="locator", help="pgsql database")

	args=parser.parse_args()

	build_dataset(args)
