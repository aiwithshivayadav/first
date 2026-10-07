# Hotel photos

One folder per hotel, named by the hotel's slug (see `data/image_sources.csv` for the
exact folder name of each hotel). Drop photos in and rerun `python3 tools/build_hotels.py`;
the catalogue page and the JSON/CSV pick them up automatically.

- Files are sorted by name, so prefix them to control order: `01-exterior.jpg`,
  `02-pool.jpg`, `03-room.jpg`. The first file becomes the cover image.
- Accepted formats: `.jpg`, `.jpeg`, `.png`, `.webp`, `.avif`.
- Recommended size: 1600 px wide or wider, landscape (16:9 works best for the cover),
  under 500 KB each after compression.
- Use photos you have rights to publish: the hotel's own marketing images supplied
  through Stayconnect, or images from the hotel's official website with their permission.
  Do not copy photos from MakeMyTrip, Booking.com or other booking sites.

Until a folder has photos, the page shows a labelled "Photo coming soon" placeholder.
