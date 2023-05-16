import contextlib
import subprocess
import psutil
import time
import matplotlib.pyplot as plt
import numpy as np

def avg_time_test():
    maxold = 0
    maxonto = 0
    totaltimeold = 0
    totaltimeonto = 0
    oldcmd = ["python", "mainold.py", "evaluation/astrea_test/time/mapping.ttl"]
    ontocmd = ["python", "main.py", "-o", "ontologies", "evaluation/astrea_test/time/mapping.ttl"]
    for _ in range(50):
        start = time.time()
        p = subprocess.Popen(oldcmd, shell=True)
        while p.poll() is None:
            with contextlib.suppress(Exception):
                continue
        ptime = round(time.time() - start, 1)
        if ptime > maxold:
            maxold = ptime
        totaltimeold += ptime

        start2 = time.time()
        p2 = subprocess.Popen(ontocmd, shell=True)
        while p2.poll() is None:
            with contextlib.suppress(Exception):
                continue
        ptime2 = round(time.time() - start2, 1)
        if ptime2 > maxonto:
            maxonto = ptime2
        totaltimeonto += ptime2
    avgold = totaltimeold/50
    avgonto = totaltimeonto/50
    print(f"Old| avg: {avgold}s, max:{maxold}s ")
    print(f"Onto| avg: {avgonto}s, max:{maxonto}s ")



def graphs():
    # different amounts of prefixes
    self1 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping.ttl"]
    self2 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping2.ttl"]
    self3 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping3.ttl"]
    self4 = ["python", "mainold.py", "evaluation/astrea_test/self2/mapping4.ttl"]

    self6 = ["python", "main.py", "evaluation/astrea_test/self2/mapping.ttl"]
    self7 = ["python", "main.py", "evaluation/astrea_test/self2/mapping2.ttl"]
    self8 = ["python", "main.py", "evaluation/astrea_test/self2/mapping3.ttl"]
    self9 = ["python", "main.py", "evaluation/astrea_test/self2/mapping4.ttl"]

    old = [self1, self2, self3, self4]
    new = [self6, self7, self8, self9]

    sizes = ["17 prefixes", "13 prefixes", "10 prefixes", "6 prefixes"]

    timelist = []
    for itemindex, item in enumerate(old):
        print(itemindex)
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage
        plt.figure(1)
        plt.plot(x, memory, label=sizes[itemindex])
        plt.legend()
        plt.xlabel('time [s]')
        plt.ylabel('Memory Usage [MiB]')

        # time
        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist.append(ptime)


    for itemindex, item in enumerate(new):
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage
        plt.figure(2)

        plt.plot(x, memory, label=sizes[itemindex])
        plt.legend()
        plt.xlabel('time [s]')
        plt.ylabel('Memory Usage [MiB]')

        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist.append(ptime)


    # different file sizes
    self1 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping.ttl"]
    self2 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping3.ttl"]
    self3 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping4.ttl"]
    self4 = ["python", "mainold.py", "evaluation/astrea_test/self/mapping5.ttl"]

    self6 = ["python", "main.py", "evaluation/astrea_test/self/mapping.ttl"]
    self7 = ["python", "main.py", "evaluation/astrea_test/self/mapping3.ttl"]
    self8 = ["python", "main.py", "evaluation/astrea_test/self/mapping4.ttl"]
    self9 = ["python", "main.py", "evaluation/astrea_test/self/mapping5.ttl"]

    old = [self1, self2, self3, self4]
    new = [self6, self7, self8, self9]

    sizes2 = ["76KB", "50KB", "34KB", "11KB"]

    timelist2 = []
    for itemindex, item in enumerate(old):
        print(itemindex)
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage
        plt.figure(3)
        plt.plot(x, memory, label=sizes2[itemindex])
        plt.legend()
        plt.xlabel('time [s]')
        plt.ylabel('Memory Usage [MiB]')

        # time
        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist2.append(ptime)


    for itemindex, item in enumerate(new):
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage
        plt.figure(4)

        plt.plot(x, memory, label=sizes2[itemindex])
        plt.legend()
        plt.xlabel('time [s]')
        plt.ylabel('Memory Usage [MiB]')

        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist2.append(ptime)


    for i in range(len(timelist)):
        ver = 'old' if i < 4 else 'new'
        print(ver, sizes[i % 4], ':', timelist[i], 's')

    for i in range(len(timelist)):
        ver = 'old' if i < 4 else 'new'
        print(ver, sizes2[i % 4], ':', timelist2[i], 's')

    plt.show()

def avg_time_test2():
    maxold = 0
    maxonto = 0
    maxshaclgen = 0
    totaltimeold = []
    totaltimeonto = []
    totaltimeshaclgen = []
    oldcmd = ["python", "mainold.py", "evaluation/astrea_test/time/mapping.ttl"]
    shaclgencmd = ["shaclgen", "-o", "evaluation/astrea_test/time/time.ttl", "evaluation/astrea_test/time/mapping.ttl"]
    ontocmd = ["python", "main.py", "-o", "ontologies", "evaluation/astrea_test/time/mapping.ttl"]
    for _ in range(50):
        start = time.time()
        p = subprocess.Popen(oldcmd, shell=True)
        while p.poll() is None:
            with contextlib.suppress(Exception):
                continue
        ptime = time.time() - start
        if ptime > maxold:
            maxold = ptime
        totaltimeold += [ptime]

        start2 = time.time()
        p2 = subprocess.Popen(ontocmd, shell=True)
        while p2.poll() is None:
            with contextlib.suppress(Exception):
                continue
        ptime2 = time.time() - start2
        if ptime2 > maxonto:
            maxonto = ptime2
        totaltimeonto += [ptime2]

        start3 = time.time()
        p3 = subprocess.Popen(shaclgencmd, shell=True)
        while p3.poll() is None:
            with contextlib.suppress(Exception):
                continue
        ptime3 = time.time() - start3
        if ptime3 > maxshaclgen:
            maxshaclgen = ptime3
        totaltimeshaclgen += [ptime3]

    avgold = sum(totaltimeold) / len(totaltimeold)
    avgonto = sum(totaltimeonto) / len(totaltimeonto)
    avgshaclgen = sum(totaltimeshaclgen) / len(totaltimeshaclgen)
    plt.figure(1)
    plt.scatter(range(len(totaltimeonto)), totaltimeonto, label='ontology enriched RML2SHACL')
    plt.axhline(avgonto, color='b', linestyle='--', label='ontology enriched RML2SHACL average')
    plt.scatter(range(len(totaltimeshaclgen)), totaltimeshaclgen, label='shaclgen')
    plt.axhline(avgshaclgen, color='r', linestyle='--', label='shaclgen average')
    plt.scatter(range(len(totaltimeold)), totaltimeold, label='original RML2SHACL')
    plt.axhline(avgold, color='g', linestyle='--', label='original RML2SHACL average')
    plt.xlabel('Iteration')
    plt.ylabel('Time [s]')
    plt.legend()
    print(f"rml2shacl| avg: {avgold}s, max:{maxold}s ")
    print(f"rml2shacl+| avg: {avgonto}s, max:{maxonto}s ")
    print(f"shaclgen| avg: {avgshaclgen}s, max:{maxshaclgen}s ")
    plt.show()

def graphs2():
    self1 = ["shaclgen", "-o", "evaluation/astrea_test/time/time.ttl", "evaluation/astrea_test/time/mapping.ttl"]

    self6 = ["python", "main.py", "-o", "ontologies", "evaluation/astrea_test/time/mapping.ttl"]

    old = [self1]
    new = [self6]

    sizes = ["Time", "13 prefixes", "10 prefixes", "6 prefixes"]

    timelist = []

    for itemindex, item in enumerate(new):
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage

        plt.plot(x, memory, label='ontology enriched RML2SHACL')

        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist.append(ptime)

    for itemindex, item in enumerate(old):
        print(itemindex)
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage
        plt.figure(1)
        plt.plot(x, memory, label='shaclgen')
        plt.legend()
        plt.xlabel('time [s]')
        plt.ylabel('Memory Usage [MiB]')

        # time
        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist.append(ptime)

    plt.show()

def avg_time_test3():
    maxold = 0
    maxonto = 0
    totaltimeold = []
    totaltimeonto = []
    oldcmd = ["python", "mainold.py", "evaluation/astrea_test/time/mapping.ttl"]
    ontocmd = ["python", "main.py", "-s", "schemas", "evaluation/astrea_test/time/mapping.ttl"]
    for _ in range(50):
        start = time.time()
        p = subprocess.Popen(oldcmd, shell=True)
        while p.poll() is None:
            with contextlib.suppress(Exception):
                continue
        ptime = time.time() - start
        if ptime > maxold:
            maxold = ptime
        totaltimeold += [ptime]

        start2 = time.time()
        p2 = subprocess.Popen(ontocmd, shell=True)
        while p2.poll() is None:
            with contextlib.suppress(Exception):
                continue
        ptime2 = time.time() - start2
        if ptime2 > maxonto:
            maxonto = ptime2
        totaltimeonto += [ptime2]

    avgold = sum(totaltimeold) / len(totaltimeold)
    avgonto = sum(totaltimeonto) / len(totaltimeonto)
    plt.figure(1)
    plt.scatter(range(len(totaltimeonto)), totaltimeonto, label='schema enriched RML2SHACL')
    plt.axhline(avgonto, color='b', linestyle='--', label='schema enriched RML2SHACL average')
    plt.scatter(range(len(totaltimeold)), totaltimeold, label='original RML2SHACL')
    plt.axhline(avgold, color='r', linestyle='--', label='original RML2SHACL average')
    plt.xlabel('Iteration')
    plt.ylabel('Time [s]')
    plt.legend()
    print(f"rml2shacl| avg: {avgold}s, max:{maxold}s ")
    print(f"rml2shacl+| avg: {avgonto}s, max:{maxonto}s ")
    plt.show()

def graphs3():
    self1 = ["python", "mainold.py", "evaluation/xsd_test/person/mapping.ttl"]

    self6 = ["python", "main.py", "-s", "schemas", "evaluation/xsd_test/person/mapping.ttl"]

    old = [self1]
    new = [self6]

    timelist = []

    for itemindex, item in enumerate(new):
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage

        plt.plot(x, memory, label='schema enriched RML2SHACL')

        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist.append(ptime)

    for itemindex, item in enumerate(old):
        print(itemindex)
        memory = []
        p = subprocess.Popen(item, shell=True)
        current_process = psutil.Process(p.pid)
        children = psutil.Process(p.pid).children(recursive=True)
        start = time.time()
        while p.poll() is None:
            try:
                currentmem = current_process.memory_info()[0]
                for child in current_process.children(recursive=True):
                    currentmem += child.memory_info()[0]
                currentmem = (currentmem / 1024 ** 2)
                memory.append(currentmem)
                continue

            except:
                pass

        ptime = round(time.time() - start, 1)
        x = np.linspace(0, ptime, len(memory))

        # Memory usage
        plt.figure(1)
        plt.plot(x, memory, label='original RML2SHACL')
        plt.legend()
        plt.xlabel('time [s]')
        plt.ylabel('Memory Usage [MiB]')

        # time
        print('----------------------------------')
        print(f"Total execution time in seconds: {ptime}s")
        timelist.append(ptime)

    plt.show()

# avg_time_test3()
graphs3()