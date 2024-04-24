set term epscairo enhanced size 8in, 3.5in background rgb 'white'
set output "figure_12_b.eps"

dir_exists(dir) = system("[ -d '".dir."' ] && echo '1' || echo '0'") + 0

VANILLA_exists = dir_exists("./HTAP_results/latest/results_VANILLA")
DIVA_exists = dir_exists("./HTAP_results/latest/results_DIVA")
LOCATOR_H_exists = dir_exists("./HTAP_results/latest/results_LOCATOR_H")
LOCATOR_F_exists = dir_exists("./HTAP_results/latest/results_LOCATOR_F")

set logscale y 10

set xrange [0.4:8.6]
set yrange [0.5:800]

set ylabel "Query latency (sec)" font "calibri, 22" offset -3.5, -5

set multiplot

set ytics nomirror ("0.1"0.1, "1"1, "10"10, "100"100) font "calibri, 20" scale 0.0
unset xtics

set lmargin at screen 0.1
set rmargin at screen 0.99
set tmargin at screen 1. - 0.075
set bmargin at screen 1. - 0.475

set style data histograms
set style line 1 dt 3 lw 5 lc rgb 'black'

set style arrow 1 heads size screen 0.008,90 ls 2 dt 1 lw 3 lc rgb "#000000"
set style arrow 2 heads filled size 0.04, 50 ls 2 dt 1 lw 3 lc rgb "#000000"
set style arrow 3 nohead ls 7 lt 3 dt 2 lw 2 lc rgb "#222222"
set style textbox opaque noborder margins 0, 1

unset xlabel

set style fill solid 1.00 border -1
set boxwidth 0.18

set grid y lw 5
plot NaN notitle
unset grid
unset ytics
unset ylabel

set xtics font "calibri, 20" scale 0.0

if ( VANILLA_exists ) plot "<(sed -n '2,9p' ./HTAP_results/latest/results_VANILLA/query_latency.txt)" using ($1 - 0.325):($2) with boxes fs solid lt rgb "#cccccc" notitle
if ( DIVA_exists ) plot "<(sed -n '2,9p' ./HTAP_results/latest/results_DIVA/query_latency.txt)" using ($1 - 0.11):($2) with boxes fs solid lt rgb "#aaaaaa" notitle
if ( LOCATOR_H_exists ) plot "<(sed -n '2,9p' ./HTAP_results/latest/results_LOCATOR_H/query_latency.txt)" using ($1 + 0.11):($2) with boxes fs solid lt rgb "#666666" notitle
if ( LOCATOR_F_exists ) plot "<(sed -n '2,9p' ./HTAP_results/latest/results_LOCATOR_F/query_latency.txt)" using ($1 + 0.325):($2) with boxes fs solid lt rgb "#000000" notitle

if ( DIVA_exists && LOCATOR_F_exists ) plot "<(sed -n '2,9p' ./HTAP_results/latest/results_DIVA/query_latency.txt)" using ($1 - 0.11):($2):(0.325 + 0.11):(0) with vectors arrowstyle 3 notitle, \
	 "<(join ./HTAP_results/latest/results_DIVA/query_latency.txt ./HTAP_results/latest/results_LOCATOR_F/query_latency.txt | sed -n '2,9p')" using ($1 + 0.325):($6):(0):(($2 - $6)) with vectors arrowstyle 2 notitle, \
	 "<(join ./HTAP_results/latest/results_DIVA/query_latency.txt ./HTAP_results/latest/results_LOCATOR_F/query_latency.txt | sed -n '2,9p')" using ($1 + 0.325):(10 ** ((log10($2) + log10($6)) / 2)):(sprintf("%.0fx", $2 / $6)) with labels boxed center font ",20" notitle

unset xtics

set key reverse Left samplen 3 font "calibri, 22"
set key at 2.2, 3000
plot "" using ($1):(0) with boxes fs solid lt rgb "#cccccc" title "Vanilla"
set key at 3.8, 3000
plot "" using ($1):(0) with boxes fs solid lt rgb "#aaaaaa" title "w/ DIVA"
set key at 6.2, 3000
plot "" using ($1):(0) with boxes fs solid lt rgb "#666666" title "w/ LOCATOR-H"
set key at 8.7, 3000
plot "" using ($1):(0) with boxes fs solid lt rgb "#000000" title "w/ LOCATOR-F"

set tmargin at screen 1. - 0.475
set bmargin at screen 1. - 0.87

set xrange [-0.6:7.6]
set yrange [0.5:1500]
set ytics nomirror ("0.1"0.1, "1"1, "10"10, "100"100) font "calibri, 20" scale 0.0

set style fill solid 1.00 border -1
set boxwidth 0.18

set grid y lw 5
plot NaN notitle
unset grid
unset ytics
unset xlabel
unset ylabel

if ( VANILLA_exists ) plot "<(sed -n '10,17p' ./HTAP_results/latest/results_VANILLA/query_latency.txt)" using ($0 - 0.325):($2) with boxes fs solid lt rgb "#cccccc" notitle
if ( DIVA_exists ) plot "<(sed -n '10,17p' ./HTAP_results/latest/results_DIVA/query_latency.txt)" using ($0 - 0.11):($2) with boxes fs solid lt rgb "#aaaaaa" notitle
if ( LOCATOR_H_exists ) plot "<(sed -n '10,17p' ./HTAP_results/latest/results_LOCATOR_H/query_latency.txt)" using ($0 + 0.11):($2) with boxes fs solid lt rgb "#666666" notitle
if ( LOCATOR_F_exists ) plot "<(sed -n '10,17p' ./HTAP_results/latest/results_LOCATOR_F/query_latency.txt)" using ($0 + 0.325):($2) with boxes fs solid lt rgb "#000000" notitle

set xlabel "TPC-CH Query #" font "calibri, 22" offset 0, -0.1
set xtics font "calibri, 20" scale 0.0
plot "" using ($0):(0):xtic(sprintf("%d", $1)) with boxes notitle
unset xlabel
unset xtics

if ( DIVA_exists && LOCATOR_F_exists ) plot "<(sed -n '10,17p' ./HTAP_results/latest/results_DIVA/query_latency.txt)" using ($0 - 0.11):($2):(0.325 + 0.11):(0) with vectors arrowstyle 3 notitle, \
	 "<(join ./HTAP_results/latest/results_DIVA/query_latency.txt ./HTAP_results/latest/results_LOCATOR_F/query_latency.txt | sed -n '10,17p')" using ($0 + 0.325):($6):(0):(($2 - $6)) with vectors arrowstyle 2 notitle, \
	 "<(join ./HTAP_results/latest/results_DIVA/query_latency.txt ./HTAP_results/latest/results_LOCATOR_F/query_latency.txt | sed -n '10,17p')" using ($0 + 0.325):(10 ** ((log10($2) + log10($6)) / 2)):(sprintf("%.0fx", $2 / $6)) with labels boxed center font ",20" notitle

