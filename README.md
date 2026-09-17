# Job Tech Trends


## Description
Analyze and visualize the most in-demand technologies in the job market.


## Technologies Used
- Python
- AI integration
- Scrapy
- Pytest
- Pandas
- Matplotlib
- ETL


## Features
- Scrape data from job platforms.
- Analyze main technologies words from description with Gemini AI.
- Create visualization of most essential technologies.


## Setup
To install the project locally on your computer, execute the following commands in a terminal:
```bash
git clone https://github.com/Illya-Maznitskiy/job-tech-trends.git
cd job-tech-trends
python -m venv venv
venv\Scripts\activate (on Windows)
source venv/bin/activate (on macOS)
pip install -r requirements.txt
```


## Check .env.example
Check [.env.example](.env.example) file  
Create your .env file and set vars by their simple guide


## Run the app
Open the terminal and use the following command:  
(Average execution time: ~0.3 s / job)
```bash
python main.py
```
Note: Google AI models can make mistakes, so double-check responses before relying on, publishing, or otherwise using generated content.


## Testing
Test coverage ~ 90%  
Open the terminal and use the following command:
```bash
pytest
flake8
```

## Check the result
To check the result open the path:
[analytics/data/tech_counts_plot.png](analytics/data/tech_counts_plot.png)


# Screenshots

### Logging
![Scraping Data](screenshots/logging.png)

### Test Coverage
![Scraping Data](screenshots/tests_coverage.png)

### Visualization result
![Visualization result](screenshots/top_technologies.png)
