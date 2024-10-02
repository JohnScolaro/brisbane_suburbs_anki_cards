import genanki
import os

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



current_file_path = os.path.dirname(os.path.abspath(__file__))

# Initialize the Anki deck
my_deck = genanki.Deck(DECK_ID, DECK_NAME)
media_files = []

# Loop over all images in the output folder and add them to the deck
for root, dirs, files in os.walk(os.path.join('output', 'Brisbane City')):
    for file in files:
        if file.endswith(".jpg"):
            # The image path is the media file
            image_path = os.path.join(root, file)
            full_image_path = os.path.join(os.path.dirname(__file__), image_path)

            # Extract locality name from file name (remove .jpg extension)
            locality = os.path.splitext(file)[0]
            
            # Add the image and locality to the Anki deck
            my_note = genanki.Note(
                model=my_model,
                fields=[f'<img src="{file}">', locality]
            )
            my_deck.add_note(my_note)
            media_files.append(image_path)

# Generate the Anki package
output_anki_file = 'suburb_maps.apkg'
my_package = genanki.Package(my_deck)
my_package.media_files = media_files  # Add media files
my_package.write_to_file(output_anki_file)

print(f"Anki deck created and saved as {output_anki_file}")