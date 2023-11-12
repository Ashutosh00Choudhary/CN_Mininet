from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import argparse
import subprocess
import time
import matplotlib.pyplot as plt
import re
import os

def plot_throughput(file_path, save_path=None):
    with open(file_path, 'r') as file:
        data = file.read()

    time_values = re.findall(r'-(\d+\.\d+) ', data)
    throughput_values = re.findall(r'(\d*\.?\d*) GBytes/sec', data)

    time_values = [0] + [float(i) for i in time_values]
    throughput_values = [0] + [float(i) for i in throughput_values]

    plt.figure()
    plt.plot(time_values, throughput_values, marker='o')
    plt.title('Time vs Throughput')
    plt.xlabel('Time Interval (sec)')
    plt.ylabel('Throughput (Gbits/sec)')
    plt.grid(True)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

class MyTopo(Topo):
    def __init__(self):
        Topo.__init__(self)
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        self.addLink(h1, s1, cls=TCLink)
        self.addLink(h2, s1, cls=TCLink)
        self.addLink(h3, s2, cls=TCLink)
        self.addLink(h4, s2, cls=TCLink)
        self.addLink(s1, s2, cls=TCLink)

def start_iperf_server(host, server_file, congestion="bbr"):
    server_cmd = f'iperf -s -t 5 -i 0.1 -p 5001 -f G -Z {congestion} > {server_file}'
    print(server_cmd)
    return host.popen(server_cmd, shell=True)

def start_iperf_client(host, client_file, congestion="bbr", hostip=""):
    client_cmd = f'iperf -c {hostip} -t 5 -i 0.1 -p 5001 -f G -Z {congestion} > {client_file}'
    print(client_cmd)
    client_process = host.popen(client_cmd, shell=True)
    return client_process

def add_loss(net, s1, s2, loss):
    for intf in net[s1].intfList():
        if intf.link and s2 in (intf.link.intf1.name, intf.link.intf2.name):
            intf.link.intf1.config(cls=TCLink, loss=loss)
            intf.link.intf2.config(cls=TCLink, loss=loss)
            info(f"Setting loss to {loss}% for link between {intf.link.intf1.name} and {intf.link.intf2.name}\n")

def main():
    parser = argparse.ArgumentParser(description="Mininet Example")
    parser.add_argument("--config", help="Configuration parameter")
    parser.add_argument("--congestion", help="Congestion control scheme")
    parser.add_argument("--loss", help="Link speed in Mbps")
    
    args = parser.parse_args()
    
    if args.config is None:
        print("Please provide a configuration parameter like --config a  --config b or --config c")
        return 0
    
    if args.config == 'a' and args.congestion not in ["reno", "cubic", "bbr", "vegas"]:
        print("Please provide a valid congestion parameter like --congestion reno or --congestion cubic or --congestion bbr or --congestion vegas")
        return 0

    print(args.config, args.congestion, args.loss)

    topo = MyTopo()
    net = Mininet(topo)
    net.start()

    if args.loss:
        add_loss(net, 's1', 's2', int(args.loss))

    if args.config == 'b':
        for host in ['h1', 'h4']:
            os.makedirs(f"./b/text/{host}", exist_ok=True)
        congestion_arr = ["reno", "cubic", "bbr", "vegas"]
        print("Config b: h4 as the server and h1 as the client")
        for congestion in congestion_arr:
            print(f"********* {congestion} *********")
            h4_server_file = f"./b/text/h4/b_h4_server_{congestion}.txt"
            server_process = start_iperf_server(net['h4'], h4_server_file, congestion)
            time.sleep(1)
            h1_client_file = f"./b/text/h1/b_h1_client_{congestion}.txt"
            client_process = start_iperf_client(net['h1'], h1_client_file, congestion, "10.0.0.4")
            server_process.wait()
            client_process.wait()
            print("********* plotting h1 client throughput")
            plot_throughput(h1_client_file, f"./b/plots/h1/h1_client_{congestion}.png")
            plot_throughput(h4_server_file, f"./b/plots/h4/h4_server_{congestion}.png")

    if args.config == 'c':
        for host in ['h1', 'h2', 'h3', 'h4']:
            os.makedirs(f"./c/text/{host}", exist_ok=True)
        congestion_arr = ["reno", "cubic", "bbr", "vegas"]
        print("Config c: h1,h2,h3 as the client and h4 as the server")
        for congestion in congestion_arr:
            print(f"********* {congestion} *********")
            h4_server_file = f"./c/text/h4/c_h4_server_{congestion}.txt"
            server_process = start_iperf_server(net['h4'], h4_server_file, congestion)
            time.sleep(1)
            h2_client_file = f"./c/text/h2/c_h2_client_{congestion}.txt"
            h2_client_process = start_iperf_client(net['h2'], h2_client_file, congestion, "10.0.0.4")
            h1_client_file = f"./c/text/h1/c_h1_client_{congestion}.txt"
            h1_client_process = start_iperf_client(net['h1'], h1_client_file, congestion, "10.0.0.4")
            h3_client_file = f"./c/text/h3/c_h3_client_{congestion}.txt"
            h3_client_process = start_iperf_client(net['h3'], h3_client_file, congestion, "10.0.0.4")
            server_process.wait()
            h1_client_process.wait()
            h2_client_process.wait()
            h3_client_process.wait()
            plot_throughput(h1_client_file, f"./c/plots/h1/h1_client_{congestion}.png")
            plot_throughput(h2_client_file, f"./c/plots/h2/h2_client_{congestion}.png")
            plot_throughput(h3_client_file, f"./c/plots/h3/h3_client_{congestion}.png")
            plot_throughput(h4_server_file, f"./c/plots/h4/h4_server_{congestion}.png")

    if args.config == 'a':
        for host in ['h1', 'h2', 'h3', 'h4']:
            os.makedirs(f"./a/text/{host}", exist_ok=True)
        congestion = args.congestion
        os.makedirs(f"./a/text/h1", exist_ok=True)
        print(f"********* {congestion} *********")
        h4_server_file = f"./a/text/h4/a_h4_server_{congestion}.txt"
        server_process = start_iperf_server(net['h4'], h4_server_file, congestion)
        time.sleep(1)
        h2_client_file = f"./a/text/h2/a_h2_client_{congestion}.txt"
        h2_client_process = start_iperf_client(net['h2'], h2_client_file, congestion, "10.0.0.4")
        h1_client_file = f"./a/text/h1/a_h1_client_{congestion}.txt"
        h1_client_process = start_iperf_client(net['h1'], h1_client_file, congestion, "10.0.0.4")
        h3_client_file = f"./a/text/h3/a_h3_client_{congestion}.txt"
        h3_client_process = start_iperf_client(net['h3'], h3_client_file, congestion, "10.0.0.4")
        server_process.wait()
        h1_client_process.wait()
        h2_client_process.wait()
        h3_client_process.wait()
        plot_throughput(h1_client_file, f"./a/plots/h1/h1_client_{congestion}.png")
        plot_throughput(h2_client_file, f"./a/plots/h2/h2_client_{congestion}.png")
        plot_throughput(h3_client_file, f"./a/plots/h3/h3_client_{congestion}.png")
        plot_throughput(h4_server_file, f"./a/plots/h4/h4_server_{congestion}.png")

    if args.config == 'd':
        for host in ['h1', 'h4']:
            os.makedirs(f"./d/text/{host}", exist_ok=True)
        for loss in [0, 1, 2]:
            add_loss(net, 's1', 's2', loss)
            congestion_arr = ["reno", "cubic", "bbr", "vegas"]
            print("Config d: h4 as the server and h1 as the client")
            for congestion in congestion_arr:
                print(f"********* {congestion} *********")
                h4_server_file = f"./d/text/h4/d_h4_server_{congestion}_loss_{loss}.txt"
                server_process = start_iperf_server(net['h4'], h4_server_file, congestion)
                time.sleep(1)
                h1_client_file = f"./d/text/h1/d_h1_client_{congestion}_loss_{loss}.txt"
                client_process = start_iperf_client(net['h1'], h1_client_file, congestion, "10.0.0.4")
                server_process.wait()
                client_process.wait()
                print("********* plotting h1 client throughput")
                plot_throughput(h1_client_file, f"./d/plots/h1/h1_client_{congestion}_loss_{loss}.png")
                plot_throughput(h4_server_file, f"./d/plots/h4/h4_server_{congestion}_loss_{loss}.png")

    print("Dumping host connections")
    dumpNodeConnections(net.hosts)

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
    info('Done.\n')
