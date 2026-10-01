metdata = []

try:
    with open(r"C:\Users\LENOVO\Desktop\college\metro_data.txt", "r") as file:
        next(file)

        for line in file:
            line = line.strip()

            if not line:
                continue

            fields = [l.strip() for l in line.split(",")]

            if len(fields) != 5:
                continue

            name = fields[0].strip().lower()
            nxtstat = fields[2].strip().lower()
            nxtstatkey = fields[2].strip() if nxtstat != "none" else "NA"

            metdata.append({
                "line": name,
                "station": fields[1].strip(),
                "station_key": fields[1].strip().lower(),
                "next_station": nxtstatkey,
                "travel_time": int(fields[3].strip()) if fields[3].strip() else 0,
                "interchange": fields[4].strip().lower() == "yes"
            })

except FileNotFoundError:
    print("file not found")


map = {}

for rec in metdata:
    lines = rec["line"]
    skey = rec["station_key"]

    if lines not in map:
        map[lines] = []

    if skey not in map[lines]:
        map[lines].append(skey)


bluevaishali = set([
    "dwarka sector 21", "dwarka sector 8", "dwarka sector 9",
    "dwarka sector 10", "dwarka sector 11", "dwarka sector 12",
    "dwarka sector 13", "dwarka sector 14", "dwarka",
    "dwarka mor", "nawada", "uttam nagar west", "uttam nagar east",
    "janakpuri west", "janakpuri east", "tilak nagar",
    "subhash nagar", "tagore garden", "rajouri garden",
    "ramesh nagar", "moti nagar", "kirti nagar", "shadipur",
    "patel nagar", "rajendra place", "karol bagh", "jhandewalan",
    "ramakrishna ashram marg", "rajiv chowk", "barakhamba road",
    "mandi house", "supreme court", "indraprastha", "yamuna bank",
    "laxmi nagar", "nirman vihar", "preet vihar", "karkarduma",
    "anand vihar isbt", "kaushambi", "vaishali"
])

blueNoida = set([
    "yamuna bank", "akshardham", "mayur vihar 1",
    "mayur vihar extension", "new ashok nagar", "noida sector 15",
    "noida sector 16", "noida sector 18", "botanical garden",
    "golf course", "noida city centre", "sector 34 noida",
    "sector 52 noida", "sector 61 noida", "sector 59 noida",
    "sector 62 noida", "noida electronic city"
])


if "blue_vaishali" not in map:
    map["blue_vaishali"] = []

if "blue_noida" not in map:
    map["blue_noida"] = []


for rec in metdata:
    if rec["line"] == "blue":
        skey = rec["station_key"]

        if skey in bluevaishali and skey not in map["blue_vaishali"]:
            map["blue_vaishali"].append(skey)

        if skey in blueNoida and skey not in map["blue_noida"]:
            map["blue_noida"].append(skey)


if "yamuna bank" in map["blue_vaishali"] and "yamuna bank" not in map["blue_noida"]:
    map["blue_noida"].insert(0, "yamuna bank")

if "yamuna bank" in map["blue_noida"] and "yamuna bank" not in map["blue_vaishali"]:
    map["blue_vaishali"].append("yamuna bank")


travelltime = {}

for rec in metdata:
    lines = rec["line"]
    sk = rec["station_key"]
    nxt = rec["next_station"].lower()

    if nxt != "na":
        tt = rec["travel_time"]
        travelltime[(lines, sk, nxt)] = tt
        travelltime[(lines, nxt, sk)] = tt


statline = {}

for rec in metdata:
    sk = rec["station_key"]
    lines = rec["line"]

    if sk not in statline:
        statline[sk] = []

    if lines not in statline[sk]:
        statline[sk].append(lines)


if "yamuna bank" not in statline:
    statline["yamuna bank"] = []

if "blue" not in statline["yamuna bank"]:
    statline["yamuna bank"].append("blue")


interchanges = {}

for rec in metdata:
    if rec["interchange"]:
        sk = rec["station_key"]

        if sk not in interchanges:
            interchanges[sk] = []

        if rec["line"] not in interchanges[sk]:
            interchanges[sk].append(rec["line"])


for st, lines in statline.items():
    if len(lines) > 1:
        if st not in interchanges:
            interchanges[st] = []

        for lines in lines:
            if lines not in interchanges[st]:
                interchanges[st].append(lines)


termm = {
    "blue_vaishali": ["dwarka sector 21", "vaishali"],
    "blue_noida": ["yamuna bank", "noida electronic city"],
    "red": ["rithala", "shaheed sthal new bus adda"],
    "magenta": ["janakpuri west", "botanical garden"],
    "orange": ["dwarka sector 21"]
}


def convert(t):
    try:
        h, m = [int(x) for x in t.split(":")]
        return h * 60 + m
    except ValueError as e:
        raise ValueError("Invalid time format (HH:MM required).") from e


def reverseconv(m):
    return f"{m//60:02d}:{m%60:02d}"


sercstarts = 6 * 60
serends = 23 * 60


def freqq(minute):
    if (8 * 60 <= minute <= 10 * 60) or (17 * 60 <= minute <= 19 * 60):
        return 4
    return 8


def traveltimeget(keyofline, a, b):
    return travelltime.get((keyofline, a, b), 0)


def cumtime(branch, terminal, target):
    stations = map.get(branch, [])

    if terminal not in stations or target not in stations:
        return None

    term = stations.index(terminal)
    targetind = stations.index(target)

    if term == targetind:
        return 0

    step = 1 if targetind > term else -1
    tottime = 0
    name = "blue" if branch.startswith("blue") else branch
    curr = term

    while curr != targetind:
        nextpos = curr + step
        tottime += traveltimeget(name, stations[curr], stations[nextpos])
        curr = nextpos

    return tottime


def trainarrival(branch, station, currtime):
    terminals = termm.get(branch, [])
    arrivals = []

    for terminal in terminals:
        stations = map.get(branch, [])

        if terminal not in stations or station not in stations:
            continue

        term = stations.index(terminal)
        start = stations.index(station)

        if term == start:
            direc = "Starts here"
            dest = terminals[1] if terminal == terminals[0] else terminals[0]
        else:
            dest = terminals[1] if term < start else terminals[0]
            direc = f"Towards {dest.title()}"

        travel = cumtime(branch, terminal, station)

        if travel is None:
            continue

        freq = freqq(currtime)
        depttime = sercstarts

        while depttime <= serends:
            statarrival = depttime + travel

            if statarrival > currtime and statarrival <= serends:
                arrivals.append({
                    "time": statarrival,
                    "direc": direc,
                    "terminal": terminal.title(),
                    "dest": dest.title()
                })

            depttime += freq
            freq = freqq(deptime := depttime)

    return sorted(arrivals, key=lambda x: x["time"])[:5]


def nextstattrain(branch, src, dest, currtime):
    stations = map.get(branch, [])

    if src not in stations or dest not in stations:
        return None

    srcind = stations.index(src)
    destindex = stations.index(dest)
    terminals = termm.get(branch, [])

    if not terminals:
        return None

    if srcind < destindex:
        terminal = terminals[0]
    else:
        terminal = terminals[1]

    traveltosrc = cumtime(branch, terminal, src)

    if traveltosrc is None:
        return None

    freq = freqq(sercstarts)
    depttime = sercstarts

    while depttime <= serends:
        arratsrc = depttime + traveltosrc

        if arratsrc >= currtime and arratsrc <= serends:
            srctodest = cumtime(branch, src, dest)

            if srctodest is not None:
                return arratsrc + srctodest

        depttime += freq
        freq = freqq(deptime := depttime)

    return None


def singleLine(keyofline, src, dest, starttime):
    if keyofline == "blue":
        if src in map["blue_vaishali"] and dest in map["blue_vaishali"]:
            return nextstattrain("blue_vaishali", src, dest, starttime)

        if src in map["blue_noida"] and dest in map["blue_noida"]:
            return nextstattrain("blue_noida", src, dest, starttime)

        return None

    return nextstattrain(keyofline, src, dest, starttime)


def mistofuser(s):
    s0 = s.strip().lower()

    correction = {
        "noida e city": "noida electronic city",
        "nec": "noida electronic city",
        "electronic city": "noida electronic city",
        "bg": "botanical garden",
        "botanical": "botanical garden"
    }

    return correction.get(s0, s0)


def fare(totmins):
    if totmins <= 10:
        return 10
    elif totmins <= 20:
        return 20
    elif totmins <= 30:
        return 30
    elif totmins <= 45:
        return 40
    elif totmins <= 60:
        return 50
    else:
        return 50


def nxtmet(dummyline, station, currtime):
    sk = mistofuser(station)

    if sk not in statline:
        print("station not found")
        return

    try:
        currmin = convert(currtime)
    except ValueError:
        print("invalid time format")
        return

    if currmin < sercstarts or currmin > serends:
        print("No service currently")
        return

    print(f"Next Train is at {station.title()}")
    print(f"Current Time: {currtime}\n")

    lines = statline[sk]

    for lines in lines:
        if lines == "blue":
            if sk in map.get("blue_vaishali", []):
                arrivals = trainarrival("blue_vaishali", sk, currmin)

                if arrivals:
                    print(f"Blue Line (Vaishali Branch):")

                    for i, arr in enumerate(arrivals[:5], 1):
                        print(f"  {i}. {reverseconv(arr['time'])} - {arr['direc']}")

                    print()

            if sk in map.get("blue_noida", []):
                arrivals = trainarrival("blue_noida", sk, currmin)

                if arrivals:
                    print(f"Blue Line (Noida Branch):")

                    for i, arr in enumerate(arrivals[:5], 1):
                        print(f"  {i}. {reverseconv(arr['time'])} - {arr['direc']}")

                    print()

        else:
            arrivals = trainarrival(lines, sk, currmin)

            if arrivals:
                print(f"{lines.title()} Line:")

                for i, arr in enumerate(arrivals[:5], 1):
                    print(f"  {i}. {reverseconv(arr['time'])} - {arr['direc']}")

                print()


def interchange(linefrom, lineto, src, dest, startmin):
    inter = []

    for st, lines in interchanges.items():
        if linefrom in lines and lineto in lines:
            inter.append(st)

    if linefrom == "blue" and lineto == "blue":
        inter = ["yamuna bank"]

    best = None
    bestfir = None
    bestinters = ""

    for inter in inter:
        if linefrom == "blue":
            branchfrom = "blue_vaishali" if src in map["blue_vaishali"] else "blue_noida"
        else:
            branchfrom = linefrom

        arrfirst = nextstattrain(branchfrom, src, inter, startmin)

        if arrfirst is None:
            continue

        arrinter = arrfirst + 3

        if lineto == "blue":
            tobranch = "blue_vaishali" if dest in map["blue_vaishali"] else "blue_noida"
        else:
            tobranch = lineto

        secarrival = nextstattrain(tobranch, inter, dest, arrinter)

        if secarrival is None:
            continue

        if best is None or secarrival < best:
            best = secarrival
            bestfir = arrfirst
            bestinters = inter

    return best, bestfir, bestinters


def twointer(src, dest, startmin):
    best = None
    bestplan = None

    souceline = statline[src]
    destline = statline[dest]
    all = set(rec['line'] for rec in metdata)
    inter = list(interchanges.keys())

    for L1 in souceline:
        for L3 in destline:
            for L2 in all:
                if L2 == L1 or L2 == L3:
                    continue

                firstcand = [
                    st for st in inter
                    if L1 in interchanges[st] and L2 in interchanges[st]
                ]

                seccand = [
                    st for st in inter
                    if L2 in interchanges[st] and L3 in interchanges[st]
                ]

                if not firstcand or not seccand:
                    continue

                for a in firstcand:
                    arr1 = singleLine(L1, src, a, startmin)

                    if arr1 is None:
                        continue

                    depart2 = arr1 + 3

                    for b in seccand:
                        arr2 = singleLine(L2, a, b, depart2)

                        if arr2 is None:
                            continue

                        depart3 = arr2 + 3
                        finalArr = singleLine(L3, b, dest, depart3)

                        if finalArr is None:
                            continue

                        if best is None or finalArr < best:
                            best = finalArr
                            bestplan = {
                                "type": "two_interchange",
                                "arrival": finalArr,
                                "A": a,
                                "B": b,
                                "L1": L1,
                                "L2": L2,
                                "L3": L3
                            }

    return best, bestplan


def planJourney(src, dest, timeStr):
    src = mistofuser(src)
    dest = mistofuser(dest)

    if src not in statline or dest not in statline:
        print("Station not found!")
        return

    try:
        startmin = convert(timeStr)
    except ValueError:
        print("Invalid time format")
        return

    souceline = statline[src]
    destline = statline[dest]

    bestplan = None
    bestarr = None

    for lines in (set(souceline) & set(destline)):
        arr = singleLine(lines, src, dest, startmin)

        if arr is not None and (bestarr is None or arr < bestarr):
            bestarr = arr
            bestplan = {
                "type": "single",
                "line": lines,
                "arrival": arr
            }

    for first in souceline:
        for last in destline:
            arr, firstLeg, inter = interchange(
                first, last, src, dest, startmin
            )

            if arr is not None and (bestarr is None or arr < bestarr):
                bestarr = arr
                bestplan = {
                    "type": "interchange",
                    "line_from": first,
                    "line_to": last,
                    "arrival": arr,
                    "first_leg_arrival": firstLeg,
                    "interchange": inter
                }

    twoset, twoplan = twointer(src, dest, startmin)

    if twoset is not None and (bestarr is None or twoset < bestarr):
        bestarr = twoset
        bestplan = twoplan

    if bestplan is None:
        print("No possible route.")
        return

    print("\n BEST ROUTE \n")

    tottimeoftravel = bestarr - startmin
    fareamt = fare(tottimeoftravel)

    if bestplan["type"] == "single":
        print(f"Direct train on {bestplan['line'].title()} Line")
        print(f" Depart {src.title()}: {timeStr}")
        print(f" Arrive {dest.title()}: {reverseconv(bestplan['arrival'])}")

    elif bestplan["type"] == "interchange":
        inter = bestplan["interchange"]
        arrivalatbranchfirst = bestplan["first_leg_arrival"]

        print(f"Branch 1: {src.title()} → {inter.title()}")
        print(f" {bestplan['line_from'].title()} Line")
        print(f" Depart: {timeStr} | Arrive: {reverseconv(arrivalatbranchfirst)}")

        print(f"\n Change trains (3 min wait) \n")

        print(f"Branch 2: {inter.title()} → {dest.title()}")
        print(f" {bestplan['line_to'].title()} Line")
        print(f" Depart: {reverseconv(arrivalatbranchfirst + 3)} | Arrive: {reverseconv(bestplan['arrival'])}")

    else:
        A = bestplan["A"]
        B = bestplan["B"]
        L1 = bestplan["L1"]
        L2 = bestplan["L2"]
        L3 = bestplan["L3"]

        arr1 = singleLine(L1, src, A, startmin)

        print(f"Branch 1: {src.title()} → {A.title()}")
        print(f" {L1.title()} Line")
        print(f" Depart: {timeStr} | Arrive: {reverseconv(arr1)}")

        print(f"\n Change trains (3 min) \n")

        depart2 = arr1 + 3
        arr2 = singleLine(L2, A, B, depart2)

        print(f"Branch 2: {A.title()} → {B.title()}")
        print(f" {L2.title()} Line")
        print(f" Depart: {reverseconv(depart2)} | Arrive: {reverseconv(arr2)}")

        print(f"\n Change trains (3 min) \n")

        depart3 = arr2 + 3

        print(f"Branch 3: {B.title()} → {dest.title()}")
        print(f" {L3.title()} Line")
        print(f" Depart: {reverseconv(depart3)} | Arrive: {reverseconv(bestplan['arrival'])}")

    print(f"Final Arrival: {reverseconv(bestarr)}")
    print(f"Total Travel Time: {tottimeoftravel} min")
    print(f"Total Fare: ₹{fareamt}")


def faremenu():
    print("\n FARE CALCULATOR ")

    src = input("Enter starting station: ")
    dest = input("Enter dest station: ")
    tm = input("Enter start time (HH:MM): ")

    src = mistofuser(src)
    dest = mistofuser(dest)

    if src not in statline or dest not in statline:
        print("One or both station names seem incorrect. Please try again.")
        return

    try:
        startmin = convert(tm)
    except ValueError:
        print("Time format looks incorrect. Please use HH:MM format.")
        return

    srcLines = statline[src]
    dstLines = statline[dest]

    bestarr = None

    for lines in set(srcLines) & set(dstLines):
        arr = singleLine(lines, src, dest, startmin)

        if arr is not None and (bestarr is None or arr < bestarr):
            bestarr = arr

    for first in srcLines:
        for last in dstLines:
            arr, fl, inter = interchange(
                first, last, src, dest, startmin
            )

            if arr is not None and (bestarr is None or arr < bestarr):
                bestarr = arr

    twoset, _ = twointer(src, dest, startmin)

    if twoset is not None and (bestarr is None or twoset < bestarr):
        bestarr = twoset

    if bestarr is None:
        print("So Sorry, no valid route could be found :()")
        return

    tottimeoftravel = bestarr - startmin
    fareamt = fare(tottimeoftravel)

    print("\nFare details of your journey are -")
    print(f"From- {src.title()}")
    print(f"To- {dest.title()}")
    print(f"Start time is- {tm}")
    print(f"Expected time of your arrival is {reverseconv(bestarr)}")
    print(f"Total time of your travel is -{tottimeoftravel} minutes")
    print(f"Total Fare for yout journey is - ₹{fareamt}")


def mainMenu():
    while True:
        print("Delhi Metro Menu")
        print(" (Which all metro lines ? : Blue / Magenta / Red / Orange Lines)")
        print("(1) Check the next metro")
        print("(2) Plan your journey")
        print("(3) Calculate fare for your travel")
        print("(4) Exit")

        ch = input("Please choose an option (1-4): ").strip()

        if ch == "1":
            station = input("\nEnter station name: ")
            time = input("Enter curr time (HH:MM): ")
            nxtmet(None, station, time)

        elif ch == "2":
            print()
            src = input("Starting station: ")
            dest = input("dest station: ")
            time = input("When do you want to start? (HH:MM): ")
            planJourney(src, dest, time)

        elif ch == "3":
            faremenu()

        elif ch == "4":
            print("Have a safe journey!\n")
            break

        else:
            print("Invalid option")


if __name__ == "__main__":
    mainMenu()