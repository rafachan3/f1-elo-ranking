from data_processor import F1DataProcessor

def main():
    processor = F1DataProcessor()
    processor.load_data()
    processor.process_races()
    rankings = processor.calculate_rankings()
    rankings.to_csv('./f1_driver_elo_rankings.csv', index=False)
    print("Elo rankings have been calculated and saved.")

if __name__ == "__main__":
    main()
