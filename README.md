# pheonix
This is our Repo for Hackkthon of TechFest. From SSRVM BN 

# IMPORTANT NOTES
- We were not able to link it to MongoDB ,So , we are running the data considering the data.json in the ***main*** branch.
- There is a strict json format to be followed while making your own data :

  """
  {
    "search-option" : {
      "name": "title of problem or solution",
      "ABOut": "brief explanation" ,
      "overview" : "Explanation" ,
      "Number of Charts" : Number:int ,
      "chartn" {
        "title": "Example activity by sector",                                            - Example
        "type": "bar graph",
        "dataset1": [24, 32, 29, 15],
        "Labels": ["Agriculture", "Industry", "Services", "Other"],
        "content": "Illustrative activity index by sector, not a share of GDP."
    }
"""

- As we dont have any direct API key or permissions to Send a request to any Government Website , we created a reports.jsonl
