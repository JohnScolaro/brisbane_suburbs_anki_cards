import pandas as pd
from bs4 import BeautifulSoup
import geopandas as gpd
from brisbane_suburbs_anki_cards import DOC_KML

def get_localities_df(filename: str) -> pd.DataFrame:
    suburb_df = gpd.read_file(filename)
    
    # Apply the function to extract locality and LGA
    suburb_df[['locality', 'lga']] = suburb_df['Description'].apply(lambda x: pd.Series(extract_locality_lga(x)))
    suburb_df = suburb_df.drop(columns=['Name', 'Description'])
    return suburb_df


# Function to extract locality and lga
def extract_locality_lga(html_description):
    soup = BeautifulSoup(html_description, 'html.parser')
    
    # Find all rows in the table
    rows = soup.find_all('tr')
    
    # Initialize variables
    locality = None
    lga = None
    
    # Iterate over rows to find locality and lga
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 2:
            header = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            if header == 'locality':
                locality = value
            elif header == 'lga':
                lga = value
    
    return locality, lga

if __name__ == "__main__":
    get_localities_df(DOC_KML)