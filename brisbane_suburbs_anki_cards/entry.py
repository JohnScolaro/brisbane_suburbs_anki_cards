from brisbane_suburbs_anki_cards.generate_anki_deck import create_anki_deck
from brisbane_suburbs_anki_cards.generate_images import create_and_save_images

def main():
    # This is the entrypoint for the whole package. This is what's ran when you
    # call `create-deck` when the package is installed.
    create_and_save_images()
    create_anki_deck()