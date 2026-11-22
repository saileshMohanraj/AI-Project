import csv
def load_visits(file_path="data/visits.csv"):
    visits=[]
    with open(file_path,"r",newline="",encoding="utf-8-sig") as file:
        reader=csv.DictReader(file)
        for row in reader:
            visits.append(row)
    return visits
if __name__=="__main__":
    data=load_visits()
    for visit in data:
        print("Total visits:",len(data))

        print("Id:",visit["id"])
        print("Arrival_time:",visit["arrival_time"])
        print("Note:",visit["note"])
        print("---------------------------------------")