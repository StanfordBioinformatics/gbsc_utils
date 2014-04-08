#!/usr/bin/env Rscript

#
# Make a detailed plot of intensity values.
#
# Usage: Rscript plot_intensity.r options
# Options:
#   datafile=filename     input data file (row=cycle, column=channel)
#   plotfile=filename     output file
#   read.starts=c(n1,n2,...) first cycle of each read
# Note that filenames and other strings must be quoted!
#

datafile <- NULL
plotfile <- NULL
read.starts <- NULL
arg.list <- commandArgs(trailingOnly=TRUE)
if (length(arg.list) == 0) {
   print("error: no arguments supplied")
   quit(save="no", status=1)
}
for (i in 1:length(arg.list)) {
    eval(parse(text=arg.list[i]))
}
if (is.null(datafile)) {
   print("error: missing datafile")
   quit(save="no", status=1)
}
if (is.null(plotfile)) {
   print("error: missing plotfile")
   quit(save="no", status=1)
}

data <- read.table(datafile, header=TRUE)
plot.width <- 100 + 10*nrow(data)
png(file=plotfile, width=plot.width, height=500, res=72)
max.intensity <- max(data)
par(mai=c(1.0,1.0,0.25,0.25))
# duplicate the last row so there is a horizontal step for the last
# data point
lastrow=nrow(data)
data = rbind(data, data.frame(a=data$a[lastrow],
                              c=data$c[lastrow],
                              g=data$g[lastrow],
                              t=data$t[lastrow]))
plot(x=c(1:nrow(data)), y=data$a, type='s', col="gray", lwd=2,
     xlab="Cycle", ylab="Intensity", ylim=c(0, max.intensity),
     xaxt='n', yaxt='n', xaxs='i', yaxs='i', xlim=c(0,nrow(data)+1),
     cex.lab=1.5)
points(x=c(1:nrow(data)), y=data$c, type='s', col="red", lwd=2)
points(x=c(1:nrow(data)), y=data$g, type='s', col="blue", lwd=2)
points(x=c(1:nrow(data)), y=data$t, type='s', col="green", lwd=2)
axis(1, 1:nrow(data))
axis(2, tck=1)
if (!is.null(read.starts)) {
   abline(v=read.starts)
}
legend("topright", c("A", "C", "G", "T"), pch=16, pt.cex=2,
       col=c("gray", "red", "blue", "green"))
