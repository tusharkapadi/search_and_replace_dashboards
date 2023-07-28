import csv
import requests
import json
import sys
from datetime import date
from datetime import datetime
import copy
import os

def search_and_replace_dashboard():

    path = createReportDir()
   
    # parse arguments
    end_point, api_token, metric_search, metric_replace, output = parse_ags()

    # query all the dashbaords from Sysdig and make a copy of it
    all_dashboards = json.loads(get_dashboards(end_point, api_token)) #this dashboard data will be updated with replaced str
    
    all_orig_dashboards = copy.deepcopy(all_dashboards) #copy of the origincal dashboards

    # iterate through all dashboards, 
    # search for given metric, 
    # replace with replace metric, 
    # prepare dashboard json, 
    # prepare list of dashboard ids found and 
    # prepare a dashboard/panel found
    after_replace_dashboards, found_dashboards_list, dashboard_ids = search_metric(all_dashboards, end_point, metric_search, metric_replace, path)
    

    # fitler the list with dashboard ids (list must contain original dashbaord jsons containing only found dashboard ids)
    before_replace_dashboards = [x for x in all_orig_dashboards["dashboards"] if x["id"] in dashboard_ids]
    
    # filter the list with dashboard ids (list must contain dashboard jsons containing only found dashboard ids) 
    after_replace_dashboards = [x for x in after_replace_dashboards["dashboards"] if x["id"] in dashboard_ids]


    replace_status_list = replace_metric(before_replace_dashboards, after_replace_dashboards, end_point, api_token, metric_search, metric_replace, path)
    
    # print summary
    print_summary_output(found_dashboards_list, replace_status_list, metric_search, len(all_dashboards['dashboards']), metric_replace)

    # create a Json file
    write_json(found_dashboards_list, metric_search, path)

    

def parse_ags():
    # usage:
    # Param 1 - Sysdig Monitor EndPoint URL
    # Param 2 - Sysdig Monitor API Token
    # Param 3 - Metric str you want to search
    # Param 4 - Metric str you want to replace

    if len(sys.argv) < 3:
        print((
                          'usage: %s sysdig_endpoint_url=<Sysdig Monitor Endpoint URL> sysdig_api_token=<Sysdig Monitor API Token> metric_search_str=<Metric you want to search in all dashboards> metric_replace_str=<Metric you want to replace with>' %
                          sys.argv[0]))
        sys.exit

    output = "csv"
    for arg in sys.argv:
        k = arg.split("=")
        if k[0] == "sysdig_endpoint_url":
            end_point = k[1]
        elif k[0] == "sysdig_api_token":
            api_token = k[1]
        elif k[0] == "metric_search_str":
            metric_search = k[1]
        elif k[0] == "metric_replace_str":
            metric_replace = k[1]
    
        sys.exit

    return end_point, api_token, metric_search, metric_replace, output


def get_dashboards(end_point, api_token):
    url = end_point + "/api/v3/dashboards/"

    payload = {}

    auth = "Bearer " + api_token
    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.ok is False:
        print("Status: received an error while getting a dashboard - " + json.dumps(response.text))

    return response.text


def search_metric(all_dashboards, end_point, metric_search, metric_replace, path):
    found_dashboards_list = []
    dashboard_ids = set()
    
    print("Searching for '" + metric_search + "' in all the dashboards....")
    
    for dashboard in all_dashboards['dashboards']:
        if metric_search in json.dumps(dashboard):
            print("X", end="", flush=True)
            # metric found... search through panels and query
            for panel in dashboard["panels"]:
                panel_str = json.dumps(panel)
                if metric_search in panel_str:
                    if "basicQueries" in panel:
                        if metric_search in json.dumps(panel["basicQueries"]):
                            for q in panel["basicQueries"]:
                                if metric_search in json.dumps(q["metrics"]):
                                    for m in q["metrics"]:
                                        if metric_search in json.dumps(m):
                                            dashboard_ids.add(dashboard["id"])
                                            metric_id = m["id"]
                                            m["id"] = m["id"].replace(metric_search, metric_replace)
                                            query_type = "Form"
                                            panel_url = end_point + "/#/dashboards/" + str(dashboard["id"]) + "/" + str(
                                                panel["id"]) + "/edit?last=600"
                                            found_dashboard_dict = {"dashboard_id": dashboard["id"], "dashboard_name": dashboard["name"], "panel_id": panel["id"],
                                                                    "panel_name": panel["name"], "panel_url": panel_url, "metric": metric_id, "replace_metric": m["id"],  "query_type": query_type}
                                            found_dashboards_list.append(found_dashboard_dict.copy())
                                            found_dashboard_dict.clear()
                    elif "advancedQueries" in panel:
                        if metric_search in json.dumps(panel["advancedQueries"]):
                            for q in panel["advancedQueries"]:
                                if metric_search in json.dumps(q["query"]):
                                    dashboard_ids.add(dashboard["id"])
                                    query = q["query"]
                                    q["query"] = q["query"].replace(metric_search, metric_replace)
                                    query_type = "PromQL"
                                    panel_url = end_point + "/#/dashboards/" + str(dashboard["id"]) + "/" + str(
                                        panel["id"]) + "/edit?last=600"
                                    found_dashboard_dict = {"dashboard_id": dashboard["id"], "dashboard_name": dashboard["name"], "panel_id": panel["id"],
                                                            "panel_name": panel["name"], "panel_url": panel_url, "query": query, "replace_query": q["query"],  "query_type": query_type}
                                    found_dashboards_list.append(found_dashboard_dict.copy())
                                    found_dashboard_dict.clear()
                                    

        else:
            print(".", end="", flush=True)

    return all_dashboards, found_dashboards_list, dashboard_ids


#def replace_metric(dashboard_ids, all_updated_dashboards, end_point, api_token, metric_search, metric_replace, path):
def replace_metric(before_replace_dashboards, after_replace_dashboards, end_point, api_token, metric_search, metric_replace, path):
    
    replace_status_dict = {}
    replace_status_list = []
    print("\n")

    if (len(after_replace_dashboards) > 0):
        print("========================================================================")
        print("'" + metric_search + "' will be replaced with '" + metric_replace + "' in the following dashboards. Please confirm for each dashboard: ")
    
    for d in after_replace_dashboards:
        replace_status_dict["dashboard_id"] = d["id"]
        print("------------------------------------------------------------------------")
        inp = input(d["name"] + " - " + str(d["id"]) + " - (Y/N): ")
        if inp == "Y":
            dashboard_data = {}
            dashboard_data["dashboard"] = [x for x in before_replace_dashboards if x["id"] == d["id"]]
            file_name = path + "/" + d["name"] + "-" + str(d["id"]) + "-before-replace.json"
            with open(file_name, 'w', encoding='UTF8', newline='') as outfile:
                outfile.write(json.dumps(dashboard_data))


            dashboard_data["dashboard"] = d
            update_dashboard(dashboard_data, end_point, api_token)
            replace_status_dict["status"] = "Replaced"
            
            file_name = path + "/" + d["name"] + "-" + str(d["id"]) + "-after-replace.json"
            with open(file_name, 'w', encoding='UTF8', newline='') as outfile:
                outfile.write(json.dumps(dashboard_data))

            print("Successully Updated")

        else:
            print("Skipped")
            replace_status_dict["status"] = "Skipped"
        
        replace_status_list.append(replace_status_dict.copy())
    return replace_status_list

# def write_csv(found_dashboards_list, metric_search, path):
#     today = date.today()
#     d1 = today.strftime("%Y-%m-%d")

#     file_name = path + "/Summary - " + metric_search + ".csv"
#     fieldnames = ['dashboard_id', 'dashboard_name', 'panel_id', 'panel_name', 'panel_url', 'query', 'replace_query', 'query_type', 'status']

#     with open(file_name, 'w', encoding='UTF8', newline='') as outfile:
#         writer = csv.DictWriter(outfile, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(found_dashboards_list)


def write_json(found_dashboards_list, metric_search, path):
    
    

    file_name = path + "/Summary - " + metric_search + ".json"
    fieldnames = ['dashboard_id', 'dashboard_name', 'panel_id', 'panel_name', 'search_metric', 'replace_metric', 'query_type', 'panel_url', 'status']

    with open(file_name, 'w', encoding='UTF8', newline='') as outfile:
        outfile.write(json.dumps(found_dashboards_list))


def print_summary_output(found_dashboards_list, replace_status_list, metric_search, total_dashboards, metric_replace):
    unique_dashboards_list = list(set([x["dashboard_name"] for x in found_dashboards_list]))

    print("")
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print("")
    print("Script attempted to search and replace - " + metric_search + " - in " + str(
        total_dashboards) + " dashboards and found in "
          + str(len(found_dashboards_list)) + " panels in " + str(len(unique_dashboards_list)) + " dashboards")

    if len(found_dashboards_list) > 0:

        # print("-" * 100)
        # print("list of all dashboards having metric - " + metric_search)
        # print("-" * 100)
        # print("\n".join(unique_dashboards_list))
        

        print("")
        print("-" * 100)
        print("list of all dashboards and panels having metric - " + metric_search + " and replacing with status")


        for dashboard in found_dashboards_list:

            for r in replace_status_list:
                if dashboard["dashboard_id"] == r["dashboard_id"]:
                    dashboard["status"] = r["status"]
                    break

            print("-" * 100)
            print("dashboard name: " + dashboard["dashboard_name"])
            print("dashboard id: " + str(dashboard["dashboard_id"]))
            print("panel id: " + str(dashboard["panel_id"]))
            if dashboard["query_type"] == "Form":
                print("metric: " + str(dashboard["metric"]))
                print("replace_metric: " + str(dashboard["replace_metric"]))
            elif dashboard["query_type"] == "PromQL":
                print("query: " + str(dashboard["query"]))
                print("replace_query: " + str(dashboard["replace_query"]))
            print("panel name: " + dashboard["panel_name"])
            print("panel url: " + dashboard["panel_url"])
            print("status: " + dashboard["status"])


def update_dashboard(dashboard_data, end_point, api_token):

    url = end_point + "/api/v3/dashboards/" + str(dashboard_data["dashboard"]["id"])

    payload = json.dumps(dashboard_data)

    auth = "Bearer " + api_token
    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    response = requests.request("PUT", url, headers=headers, data=payload)

    if response.ok:
        updated_dashboard_data = json.loads(response.text)
        dashboard_file_name = updated_dashboard_data["dashboard"]["name"] + "-" + str(updated_dashboard_data["dashboard"]["id"]) + ".json"
        #print("\nDashboard updated successfully - " + dashboard_data["dashboard"]["name"])
        # with open(dashboard_file_name,'w') as outfile:
        #     json.dump(updated_dashboard_data, outfile)

    else:
        print("Status: received an error while updating a dashboard - " + json.dumps(response.text))

def getCurrDateTime():
    now = datetime.now()
    return now.strftime("%Y-%m-%d-%H:%M:%S")

def createReportDir():

    path = os.getcwd() + "/" + getCurrDateTime()
    os.makedirs(path)
    return path

if __name__ == '__main__':
    search_and_replace_dashboard()