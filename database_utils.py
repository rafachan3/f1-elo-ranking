import pandas as pd
from flask_sqlalchemy import SQLAlchemy

def update_database_from_df(db, DriverEloRanking, df):
    for _, row in df.iterrows():
        existing_record = db.session.query(DriverEloRanking).filter_by(driver=row["Driver"]).first()
        if existing_record:
            record_changed = (
                existing_record.elo_rating != row["Elo Rating"] or
                existing_record.lower_bound != row["Lower Bound"] or
                existing_record.upper_bound != row["Upper Bound"] or
                existing_record.confidence_score != row["Confidence Score"] or
                existing_record.reliability_grade != row["Reliability Grade"] or
                existing_record.race_count != row["Race Count"] or
                existing_record.rating_volatility != row["Rating Volatility"] or
                existing_record.is_established != row["Is Established"] or
                existing_record.first_year != row["First Year"] or
                existing_record.last_year != row["Last Year"] or
                existing_record.career_span != row["Career Span"] or
                existing_record.flag_level != row["Flag Level"]
            )
            if record_changed:
                existing_record.elo_rating = row["Elo Rating"]
                existing_record.lower_bound = row["Lower Bound"]
                existing_record.upper_bound = row["Upper Bound"]
                existing_record.confidence_score = row["Confidence Score"]
                existing_record.reliability_grade = row["Reliability Grade"]
                existing_record.race_count = row["Race Count"]
                existing_record.rating_volatility = row["Rating Volatility"]
                existing_record.is_established = row["Is Established"]
                existing_record.first_year = row["First Year"]
                existing_record.last_year = row["Last Year"]
                existing_record.career_span = row["Career Span"]
                existing_record.flag_level = row["Flag Level"]
        else:
            new_record = DriverEloRanking(
                driver=row["Driver"],
                elo_rating=row["Elo Rating"],
                lower_bound=row["Lower Bound"],
                upper_bound=row["Upper Bound"],
                confidence_score=row["Confidence Score"],
                reliability_grade=row["Reliability Grade"],
                race_count=row["Race Count"],
                rating_volatility=row["Rating Volatility"],
                is_established=row["Is Established"],
                first_year=row["First Year"],
                last_year=row["Last Year"],
                career_span=row["Career Span"],
                flag_level=row["Flag Level"]
            )
            db.session.add(new_record)

    db.session.commit()