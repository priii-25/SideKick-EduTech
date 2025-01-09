import requests
import json
from datetime import datetime
import csv
import os
from time import sleep
from dotenv import load_dotenv
load_dotenv()

class JobMarketTrends:
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs"

    def get_job_trends(self, keyword, country="gb"):
        endpoint = f"{self.base_url}/{country}/search/1"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": keyword,
            "content-type": "application/json",
            "results_per_page": 50
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json(), keyword  
        except requests.exceptions.RequestException as e:
            print(f"Error fetching trends: {e}")
            return None, keyword

    def process_trends(self, trends_data, keyword):
        if not trends_data:
            return []
            
        return [{
            'skill': keyword,  
            'total_jobs': trends_data.get('count', 0),
            'mean_salary': trends_data.get('mean', 0),
            'location': trends_data.get('location', {}).get('display_name', ''),
            'date': datetime.now().strftime('%Y-%m-%d')
        }]

    def save_to_csv(self, trends, filename="market_trends.csv"):
        fieldnames = ['skill', 'total_jobs', 'mean_salary', 'location', 'date']
        
        file_exists = os.path.exists(filename)
        
        with open(filename, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(trends)

def main():
    app_id = os.getenv("app_id")
    app_key = os.getenv("app_key")
    
    tracker = JobMarketTrends(app_id, app_key)
    
    keywords = ["python", "javascript", "machine learning", "data science", "cloud computing"]
    
    for keyword in keywords:
        trends_data, keyword = tracker.get_job_trends(keyword)
        if trends_data:
            processed_trends = tracker.process_trends(trends_data, keyword)
            tracker.save_to_csv(processed_trends)
        sleep(1)

if __name__ == "__main__":
    main()