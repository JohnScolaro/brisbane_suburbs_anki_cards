import genanki
import os
from brisbane_suburbs_anki_cards.process_kml import get_localities_df
from brisbane_suburbs_anki_cards import DOC_KML
from brisbane_suburbs_anki_cards.constants import LOCAL_GOVERNMENT_AREAS_WE_CARE_ABOUT

# Anki deck metadata
DECK_NAME = "Brisbane Suburbs"
MODEL_ID = 1415815641
DECK_ID = 1884931520
NOTE_MODEL_NAME = "Image-Suburb Card"

# Define the model for Anki cards
my_model = genanki.Model(
    MODEL_ID,
    NOTE_MODEL_NAME,
    fields=[
        {'name': 'Image'},
        {'name': 'Suburb'},
    ],
    templates=[
        {
            'name': 'ImageSuburbCard',
            'qfmt': '{{Image}}',
            'afmt': '''{{FrontSide}}<hr id="answer" style="border:none;"/><div style="text-align:center; font-size: 1.5em;">{{Suburb}}</div>''',
        }
    ]
)

def create_anki_deck() -> None:
    suburb_to_cbd_mapping = get_suburb_to_due_order_mapping()

    # Initialize the Anki deck
    my_deck = genanki.Deck(DECK_ID, DECK_NAME)
    media_files = []

    # Loop over all images in the output folder and add them to the deck
    for root, dirs, files in os.walk(os.path.join('output', 'Brisbane City')):
        for file in files:
            if file.endswith(".jpg"):
                # The image path is the media file
                image_path = os.path.join(root, file)

                # Extract locality name from file name (remove .jpg extension)
                locality = os.path.splitext(file)[0]
                
                # Add the image and locality to the Anki deck
                my_note = genanki.Note(
                    model=my_model,
                    fields=[f'<img src="{file}">', locality],
                    due=suburb_to_cbd_mapping[locality]
                )
                my_deck.add_note(my_note)
                media_files.append(image_path)

    # Generate the Anki package
    output_anki_file = 'suburb_maps.apkg'
    my_package = genanki.Package(my_deck)
    my_package.media_files = media_files  # Add media files
    my_package.write_to_file(output_anki_file)

    print(f"Anki deck created and saved as {output_anki_file}")

def get_suburb_to_due_order_mapping() -> dict[str, int]:
    """
    I have found that the default order that cards are introduced is
    alphabetical, which feels like a terrible way to learn them because it's
    very hard to learn the difference between aspley, alderly, and algester,
    when you have no points of reference for any of them. I think a better way
    to learn them would be to learn them in order of distance from the CBD, so
    every time you get a new suburb, you've already learnt at least one of the
    adjacent suburbs to link it to.

    This function returns a mapping like:

    {
        'Brisbane City: 0,
        'Bowen Hills': 1,
        ...
        'Banyo': 100,
        ...
    }

    or something, so cards are introduced in order of distance to the CBD.
    """
    suburbs_df = get_localities_df(DOC_KML)

    brisbane_city_point = suburbs_df[suburbs_df['locality'] == 'Brisbane City']['geometry'].to_crs(epsg=3857).centroid

    # Reproject all geometries to the same CRS for distance calculations
    suburbs_df['geometry'] = suburbs_df['geometry'].to_crs(epsg=3857)

    # Calculate the distance of each suburb's centroid to Brisbane City's centroid
    suburbs_df['distance_to_cbd'] = suburbs_df['geometry'].centroid.apply(lambda x: x.distance(brisbane_city_point))

    # Sort the suburbs by distance to the CBD
    sorted_suburbs = suburbs_df.sort_values(by='distance_to_cbd')

    # Create a mapping of suburb names to their order in the sorted list
    suburb_to_order_mapping = { (lga, locality): order for order, (lga, locality) in enumerate(zip(sorted_suburbs['lga'], sorted_suburbs['locality'])) }

    # Only keep the suburbs in the LGA's we care about
    filtered_mapping = {locality: order for (lga, locality), order in suburb_to_order_mapping.items() if lga in LOCAL_GOVERNMENT_AREAS_WE_CARE_ABOUT}
    return filtered_mapping

if __name__ == "__main__":
    create_anki_deck()