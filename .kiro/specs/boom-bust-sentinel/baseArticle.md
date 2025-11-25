This is the article I read that was the basis of the application
https://www.noahpinion.blog/p/will-data-centers-crash-the-economy

# 1) Export prod DB URL for the Python process
export DATABASE_URL="mysql://username:password@HOST/ai-awareness?sslaccept=strict"

# 2) Run the real writer (uses FRED/alt services → writes to PlanetScale)
python scripts/store_real_data_to_planetscale.py