set term epscairo enhanced size 8in, 2.8in background rgb 'white'
set output "figure_12_a.eps"

dir_exists(dir) = system("[ -d '".dir."' ] && echo '1' || echo '0'") + 0

VANILLA_exists = dir_exists("./HTAP_results/latest/results_VANILLA")
DIVA_exists = dir_exists("./HTAP_results/latest/results_DIVA")
LOCATOR_H_exists = dir_exists("./HTAP_results/latest/results_LOCATOR_H")
LOCATOR_F_exists = dir_exists("./HTAP_results/latest/results_LOCATOR_F")

set multiplot

set lmargin at screen 0.11
set rmargin at screen 0.99

set style line 1 lc rgb '#000000' lt 4 dt 1 lw 4 pt 7 ps 1.5 pointinterval -10  # blue
set style line 2 lc rgb '#000000' lt 4 dt 9 lw 4 pt 1 ps 1.5 pointinterval -10  # blue
set style line 3 lc rgb '#888888' lt 4 dt 1 lw 4 pt 9 ps 1.5 pointinterval -10  # blue
set style line 4 lc rgb '#444444' lt 4 dt 1 lw 4 pt 2 ps 1.5 pointinterval -10  # blue

# plot 1
set tmargin at screen 1. - 0.08
set bmargin at screen 1. - 0.525
set yrange[0:1.5]
set ylabel "OLTP\ntpm (x10^6)" font "calibri, 22" offset -3.5, 0
set ytics nomirror 0.5, 0.5, 1.0 font "calibri, 20" scale 0.0 offset 0.5, 0
set xrange[0.1:1200 - 0.1]
unset xtics

set style arrow 1 heads size screen 0.008,90 ls 2 lw 3 lc rgb "#000000"
set style arrow 2 head filled size 20, 20 ls 2 lw 3 lc rgb "#000000"
set style arrow 3 heads size screen 0.008,0 ls 7 lt 3 dt 2 lw 4 lc rgb "#444444"

if ( LOCATOR_H_exists ) plot "./HTAP_results/latest/results_LOCATOR_H/tpm.txt" using ($1):($2 / 1e6) with lines ls 3 notitle
if ( LOCATOR_F_exists ) plot "./HTAP_results/latest/results_LOCATOR_F/tpm.txt" using ($1):($2 / 1e6) with linespoint ls 4 notitle
if ( DIVA_exists ) plot "./HTAP_results/latest/results_DIVA/tpm.txt" using ($1):($2 / 1e6) with linespoint ls 2 notitle
if ( VANILLA_exists ) plot "./HTAP_results/latest/results_VANILLA/tpm.txt" using ($1):($2 / 1e6) with lines ls 1 notitle

set label sprintf('OLTP') at 260, 0.15 right font "calibri, 20"
set label sprintf('HTAP') at 340, 0.15 left font "calibri, 20"
plot "" using (300):(0):(0):($2 / 1e6) with vectors arrowstyle 3 notitle, \
	 "" using (300-27.5):(0.15):(55):(0) with vectors heads filled size screen 0.008,30 lw 4 lc black notitle

unset label
unset ylabel
unset ytics

set style line 1 dt 1 lw 3 lc rgb 'black'
set style fill solid 1.00 noborder

set key reverse Left samplen 3 font "calibri, 22"
set key at 250, 1.8
plot "" using ($1):(100) with lines ls 1 title "Vanilla"
set key at 475, 1.8
plot "" using ($1):(100) with linespoint ls 2 title "w/ DIVA"
set key at 815, 1.8
plot "" using ($1):(100) with lines ls 3 title "w/ LOCATOR-H"
set key at 1175, 1.8
plot "" using ($1):(100) with linespoint ls 4 title "w/ LOCATOR-F"

# unset key
unset ylabel

# plot 2
set tmargin at screen 1. - 0.525
set bmargin at screen 1. - 0.855
set style data histograms

set yrange[0:220]
set ytics nomirror 50, 50, 150 font "calibri, 20" scale 0.0 offset 0.5, 0
set ylabel "Space\n(GiB)" font "calibri, 22" offset -3.5, 0
set xtics 300, 300, 900 scale 0.0 offset 0, 0.2 font "calibri, 20"
set xlabel "Time (sec)" offset 0, 0.2 font "calibri, 22"

if ( LOCATOR_H_exists ) plot "./HTAP_results/latest/results_LOCATOR_H/dbsize.txt" using ($1):($2 / (1024.0 * 1024)) with filledcurves above x1 lc rgb "#000000" notitle, \
	keyentry with boxes lc rgb "#000000" dt 1 title "w/ LOCATOR-H" at screen 0.53, 0.42
if ( LOCATOR_F_exists ) plot "./HTAP_results/latest/results_LOCATOR_F/dbsize.txt" using ($1):($2 / (1024.0 * 1024)) with filledcurves above x1 lc rgb "#444444" notitle, \
	keyentry with boxes lc rgb "#444444" dt 1 title "w/ LOCATOR-F" at screen 0.80, 0.42
if ( DIVA_exists ) plot "./HTAP_results/latest/results_DIVA/dbsize.txt" using ($1):($2 / (1024.0 * 1024)) with filledcurves above x1 lc rgb "#888888" notitle, \
	keyentry with boxes lc rgb "#888888" dt 1 title "w/ DIVA" at screen 0.355, 0.42
if ( VANILLA_exists ) plot "./HTAP_results/latest/results_VANILLA/dbsize.txt" using ($1):($2 / (1024.0 * 1024)) with filledcurves above x1 lc rgb "#aaaaaa" notitle, \
	keyentry with boxes lc rgb "#aaaaaa" dt 1 title "Vanilla" at screen 0.19, 0.42

unset grid
unset ylabel