# search_and_replace_dashboards

Search particular metric in all dashboards and replace with provided metric. It simply uses string to check wehther metric exists or not so it can be used for the complete metric or partial metric.

Script finds the metric and asks for the confirmation before replacing it for each dashboard.

Script creates a folder with current datetime and places all the dashbaords in json that were replaced. It stores dashboard in json before it was replaced and after it was replaced. If you have made mistake and overwrote wrong dashboard, this is the place to look for.

It creates json output file and prints the summary of dashbard/panel info with matched metric and replaced status.


### Note: Be careful replacing metric as there is not un-do avaiable. You will have to dig through dashboard jsons this script saves to revert back your changes.

This utility is written in Python3 and uses request module to query dashboards in Sysdig.

### Pre-Req:
Make sure python3 is installed.
Make sure requests module for python3 is installed
Get Sysdig Monitor API Token (Look at next slide on how to get Sysdig Monitor API Token)


### Invoke the script
Script takes 4 command line arguments as key=value pair:

 **sysdig_endpoint_url** -> Sysdig backend's SaaS endpoint URL for your account - check for more info - https://docs.sysdig.com/en/docs/administration/saas-regions-and-ip-ranges/
 
 **sysdig_api_token** -> Sysdig Monitor API Token. It will use the token to query dashbaords through REST API

 **metric_search_str** -> Metric you are interested searching in the dashboard. You don't need to specify the complete metric, partial metric name is allowed.
 
 **metric_replace_str** -> Metric you are interested replacing in the dashboard. 
 
 

```
search_and_replace_dashboard.py sysdig_endpoint_url=<sysdig_endpoint_url> sysdig_api_token=<sysdig_api_token> metric_search_str=<metric_search_str> metric_replace_str=<metric_replace_str>  

example:
python3 earch_dashboards.py sysdig_endpoint_url=https://us2.app.sysdig.com sysdig_api_token=AAAAAAAAAAAA metric_search_str=memory metric_replace_str=mem
```


### How to get Sysdig Monitor API Token:

1. Login to your Sysdig UI
2. Click on your Initial Icon at the bottom left
3. Go to Settings
4. Go to User Profile
5. Copy Sysdig Monitor API Token
