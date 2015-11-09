
setwd("~/00_Development/freetextchat")
data <- read.csv("~/00_Development/freetextchat/panlog_final.log")

data$total_clients = 1 + data$adtl_probe_clients + (data$num_adtl_rooms * data$clients_per_room)
data$total_rate = data$total_clients * data$snd_rate
data$avg_cpr = data$total_clients / (1 + data$num_adtl_rooms)

data$rate_per_room = (data$total_clients * data$snd_rate) / (1 + data$num_adtl_rooms)
data$stress_idx = data$total_rate / (1+data$num_adtl_rooms)

s1 = data[data$server_type == 1,]
s2 = data[data$server_type == 2,]

s1_10 = s1[s1$snd_rate == 10,]
r1_10 = order(s1_10$total_clients)
s1_5 = s1[s1$snd_rate == 5,]
r1_5 = order(s1_5$total_clients)
s1_1 = s1[s1$snd_rate == 1,]
r1_1 = order(s1_1$total_clients)

s2_10 = s2[s2$snd_rate == 10,]
r2_10 = order(s2_10$total_clients)
s2_5 = s2[s2$snd_rate == 5,]
r2_5 = order(s2_5$total_clients)
s2_1 = s2[s2$snd_rate == 1,]
r2_1 = order(s2_1$total_clients)

ucpr=c(25,50,75, 100)
#par(mfrow=c(length(ucpr),1), mar=c(2,3,1,1))
par(mfrow=c(2,2), mar=c(4,4,1,1))
for (i in ucpr) {
  fltr = which(s2$avg_cpr == i)
  plot(s2$total_clients[fltr],s2$max_sprocess_cpu[fltr], 
       col=c("green","red")[1+(s2$max_sprocess_cpu[fltr] > 98.5)],
       #col=c("green","red")[1+(s2$max_sprocess_cpu[fltr] > 98.5 & s2$RTT_999[fltr] > 2)],
       pch=c(1,2,0)[1+trunc(s2$snd_rate/5)],
       xlab="total clients", xlim=c(0,500), ylim=c(0,100),
       ylab="%CPU Usage",
       main=paste("cpr=",i))

  legend(300,90, pch=c(1,2,0,18,18), c("1 msg/sec", "5 msgs/sec", "10 msgs/sec","%cpu <= 98.5","%cpu > 98.5"),
         col=c("black","black","black","green","red"),
         cex=0.70,x.intersp=0.5,y.intersp=0.25,bty="n")
}

# same plots for s2 small
ucpr=c(5,10)
par(mfrow=c(2,1), mar=c(4,4,1,1))
for (i in ucpr) {
  fltr = which(s2$avg_cpr == i)
  plot(s2$total_clients[fltr],s2$max_sprocess_cpu[fltr], 
       col=c("green","red")[1+(s2$max_sprocess_cpu[fltr] > 98.5)],
       pch=c(1,2,0)[1+trunc(s2$snd_rate/5)],
       xlab="total clients", xlim=c(0,500), ylim=c(0,100),
       ylab="%CPU Usage",main=paste("cpr=",i))
 
  legend(350,100, pch=c(1,2,0,18,18), c("1 msg/sec", "5 msgs/sec", "10 msgs/sec","%cpu <= 98.5","%cpu > 98.5"),
         col=c("black","black","black","green","red"),
         cex=0.70,x.intersp=0.5,y.intersp=0.20,bty="n")
}




# Times

usr=c(1,5,10)   # sending rates
#par(mfrow=c(length(ucpr),1), mar=c(2,3,1,1))
par(mfrow=c(3,1), mar=c(4,4,1,1))
for (i in usr) {
  #fltr = which(s2$snd_rate == i) & s2$avg_cpr == 101)
  fs2 = s2[s2$max_sprocess_cpu  <=98.5 & s2$snd_rate == i ,]
  cust_ymax = 1 + (i==1)

  boxplot(fs2$RTT_max,fs2$RTT_mean,fs2$RTT_99,fs2$RTT_999,
       names=c("RTT_max","RTT_mean","RTT_99","RTT_999") , ylim=c(0,cust_ymax),
       ylab="Time (seconds)",
       main=paste("snd_rate=",i,", ",length(fs2$RTT_max),"data points"))
  print(summary(fs2$RTT_999))
}

# COMPARISON TO S1
par(mfrow=c(2,1), mar=c(3,3,1,1))

fltr = which(s1$avg_cpr == 100)

plot(s1$total_clients[fltr],s1$max_sprocess_cpu[fltr], 
     col=c("green","red")[1+(s1$max_sprocess_cpu[fltr] > 98.5)],
     pch=c(1,2,0)[1+trunc(s1$snd_rate/5)],
     xlab="total clients", xlim=c(0,500), ylim=c(0,100),
     ylab="%CPU Usage",main="Old server: dumb msg resend, cpr=100")
legend(400,90, pch=c(1,2,0,18,18), c("1 msg/sec", "5 msgs/sec", "10 msgs/sec","%cpu <= 98.5","%cpu > 98.5"),
       col=c("black","black","black","green","red"),
       cex=0.70,x.intersp=0.5,y.intersp=0.25,bty="n")

fltr = which(s2$avg_cpr == 100)
plot(s2$total_clients[fltr],s2$max_sprocess_cpu[fltr], 
     col=c("green","red")[1+(s2$max_sprocess_cpu[fltr] > 98.5)],
     pch=c(1,2,0)[1+trunc(s2$snd_rate/5)],
     xlab="total clients", xlim=c(0,500), ylim=c(0,100),
     ylab="%CPU Usage",main="New server: smart frame resend, cpr=100")

legend(400,90, pch=c(1,2,0,18,18), c("1 msg/sec", "5 msgs/sec", "10 msgs/sec","%cpu <= 98.5","%cpu > 98.5"),
       col=c("black","black","black","green","red"),
       cex=0.70,x.intersp=0.5,y.intersp=0.25,bty="n")

# this is good, and if we separate by cpr, we see less variation (thinner and more uniform
# box plots).

# usr=c(1,5,10)   # sending rates
# par(mfrow=c(length(ucpr),1), mar=c(2,3,1,1))
# par(mfrow=c(3,1), mar=c(4,4,1,1))
# for (i in usr) {
#   #fltr = which(s2$snd_rate == i) & s2$avg_cpr == 101)
#   fs2 = s2[s2$max_sprocess_cpu  <=98.5 & s2$snd_rate == i & s2$avg_cpr == 25,]
#   #cust_ymax = 1 + (i==1)
#   
#   plot(fs2$total_clients, fs2$RTT_999, 
#           ylab="RTT_999 (seconds)",xlim=c(0,500),
#           main=paste("snd_rate=",i,", ",length(fs2$RTT_max),"data points"))
# }

