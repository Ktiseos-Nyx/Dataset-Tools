"""
parameter_statistic.py

This script analyzes metadata from the ExifData Analytics project database,
generating statistics, plots, and text reports on various parameters.

Usage: Run this script directly to perform analysis on the database.
"""

import os
import re
import logging
from typing import List, Tuple, Dict, Any
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
import parameter_statistic_DB as db_module
from pathlib import Path

# Setup directories and logging
script_dir = Path(__file__).resolve().parent
logging_dir = os.path.join(script_dir, 'LOG_files')
os.makedirs(logging_dir, exist_ok=True)

logger_statistics = logging.getLogger('statistics')
logger_statistics.setLevel(logging.DEBUG)

log_file_path = os.path.join(logging_dir, "parameter_statistics_LOG.txt")
file_handler_statistics = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler_statistics.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler_statistics.setFormatter(formatter)
logger_statistics.addHandler(file_handler_statistics)

def extract_data() -> pd.DataFrame:
    """Extracts data from the database."""
    try:
        with db_module.db_connection() as conn:
            query = "SELECT file_name, file_path, last_modified, metadata, metadata_after_prompt FROM file_metadata"
            return pd.read_sql_query(query, conn)
    except Exception as e:
        logger_statistics.error(f"Error extracting data from database: {e}")
        raise

def parse_parameters(metadata: str, metadata_after_prompt: str) -> Dict[str, str]:
    """Parses parameters from metadata."""
    data = {}
    
    parameters_section = re.split(r'parameters:', metadata, flags=re.IGNORECASE)
    if len(parameters_section) > 1:
        prompt_data = parameters_section[1].strip()
        prompt_split = re.split(r'Negative prompt:', prompt_data, flags=re.IGNORECASE)
        data['prompt'] = prompt_split[0].strip() if len(prompt_split) > 1 else prompt_data
    else:
        data['prompt'] = ""
    
    negative_prompt_split = re.split(r'steps:', metadata_after_prompt, flags=re.IGNORECASE)
    data['Negative prompt'] = negative_prompt_split[0].strip() if len(negative_prompt_split) > 0 else ""

    for field in ['Sampler', 'CFG scale', 'Size', 'Model', 'VAE', 'Denoising strength']:
        match = re.search(rf'{field}: ([^,]+)', metadata_after_prompt)
        data[field] = match.group(1).strip() if match else ""
    
    return data

def parse_metadata(data_df: pd.DataFrame) -> pd.DataFrame:
    """Parses metadata from the DataFrame."""
    parsed_data = []
    for _, row in data_df.iterrows():
        parsed_params = parse_parameters(row['metadata'], row['metadata_after_prompt'])
        parsed_params['file_name'] = row['file_name']
        parsed_params['file_path'] = row['file_path']
        parsed_params['last_modified'] = row['last_modified']
        parsed_data.append(parsed_params)
    return pd.DataFrame(parsed_data)

def preprocess_text(text: str) -> str:
    """Preprocess text to treat sequences within <> and () as single entities."""
    def replace_entities(match):
        return match.group(0).replace(' ', '_')

    text = re.sub(r'<[^>]+>', replace_entities, text)
    text = re.sub(r'\([^)]+\)', replace_entities, text)
    return text

def filter_words(words: List[str]) -> List[str]:
    """Filters out single characters and common punctuation from the list of words."""
    return [word for word in words if len(word) > 1 and word not in ['.', ',', '!', '?', ':', ';', '-', '_', '(', ')']]

def analyze_all(parsed_df: pd.DataFrame) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], Dict[str, pd.Series]]:
    """Analyzes the entire dataset without specific keywords."""
    prompt_data = parsed_df['prompt'].dropna().apply(preprocess_text)
    negative_prompt_data = parsed_df['Negative prompt'].dropna().apply(preprocess_text)
    
    # Most frequent words in prompts
    prompt_words = [word for prompt in prompt_data for word in re.split(r'[,\s]+', prompt) if word]
    prompt_words = filter_words(prompt_words)
    prompt_word_counts = Counter(prompt_words).most_common()
    
    # Most frequent words in negative prompts
    negative_prompt_words = [word for prompt in negative_prompt_data for word in re.split(r'[,\s]+', prompt) if word]
    negative_prompt_words = filter_words(negative_prompt_words)
    negative_prompt_word_counts = Counter(negative_prompt_words).most_common()
    
    # Most frequent models, samplers, etc.
    parameter_counts = {field: parsed_df[field].value_counts() for field in ['Sampler', 'CFG scale', 'Size', 'Model', 'VAE', 'Denoising strength']}
    
    return prompt_word_counts, negative_prompt_word_counts, parameter_counts

def plot_word_counts(word_counts: List[Tuple[str, int]], title: str, output_dir: str, top_n: int = 20) -> None:
    """Plots word counts and saves the results."""
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(14, 8))
    
    words, counts = zip(*word_counts[:top_n])
    plt.bar(words, counts)
    plt.title(f'Frequency of {title}')
    plt.xlabel('Word')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    output_path = os.path.join(output_dir, f'{title}_counts.png')
    plt.savefig(output_path)
    plt.close()

def plot_parameter_counts(parameter_counts: Dict[str, pd.Series], output_dir: str, top_n: int = 20) -> None:
    """Plots parameter counts and saves the results."""
    os.makedirs(output_dir, exist_ok=True)
    
    for field, counts in parameter_counts.items():
        plt.figure(figsize=(14, 8))
        
        if len(counts) > top_n:
            counts = counts[:top_n]
        
        counts.plot(kind='bar')
        plt.title(f'Frequency of {field}')
        plt.xlabel(field)
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        output_path = os.path.join(output_dir, f'{field}_counts.png')
        plt.savefig(output_path)
        plt.close()

def save_word_counts_to_text(word_counts: List[Tuple[str, int]], output_path: str, title: str) -> None:
    """Saves word counts to a text file."""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(f'Analysis for {title}:\n')
        for word, count in word_counts:
            file.write(f'{word}: {count}\n')

def save_parameter_counts_to_text(parameter_counts: Dict[str, pd.Series], output_path: str) -> None:
    """Saves parameter counts to a text file."""
    with open(output_path, 'w', encoding='utf-8') as file:
        for field, counts in parameter_counts.items():
            file.write(f'Analysis for {field}:\n')
            file.write(counts.to_string())
            file.write('\n\n')

def tfidf_analysis(text_data: pd.Series, top_n: int = 20) -> Tuple[List[str], List[float]]:
    """Performs TF-IDF analysis on text data."""
    logger_statistics.debug(f"Performing TF-IDF analysis on {len(text_data)} records.")
    logger_statistics.debug(f"Sample text: {text_data.iloc[0] if not text_data.empty else 'No data'}")
    
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X = vectorizer.fit_transform(text_data)
    feature_array = vectorizer.get_feature_names_out()
    logger_statistics.debug(f"Number of features: {len(feature_array)}")
    
    if len(feature_array) == 0:
        logger_statistics.error("No features found in the text data.")
        return [], []
    
    tfidf_sorting = X.toarray().sum(axis=0).argsort()[::-1]
    top_n_words = [feature_array[i] for i in tfidf_sorting[:top_n]]
    top_n_scores = [X[:, i].sum() for i in tfidf_sorting[:top_n]]
    return top_n_words, top_n_scores

def plot_tfidf_analysis(top_n_words: List[str], top_n_scores: List[float], output_dir: str) -> None:
    """Plots TF-IDF analysis results."""
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(14, 8))
    plt.bar(top_n_words, top_n_scores)
    plt.title('Top TF-IDF Words')
    plt.xlabel('Words')
    plt.ylabel('TF-IDF Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'tfidf_analysis.png')
    plt.savefig(output_path)
    plt.close()

def save_tfidf_analysis_to_text(top_n_words: List[str], top_n_scores: List[float], output_path: str) -> None:
    """Saves TF-IDF analysis results to a text file."""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(f'TF-IDF Analysis of Prompts:\n')
        for word, score in zip(top_n_words, top_n_scores):
            file.write(f'{word}: {score}\n')

def load_keywords_from_file(file_path: str) -> List[str]:
    """Loads keywords from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            keywords = [line.strip() for line in file if line.strip()]
        return keywords
    except FileNotFoundError:
        print(f"Keyword list file not found: {default_keywords_file}")
        return []
    except Exception as e:
        print(f"Error reading Keyword list file: {e}")
        return []   


def load_default_keywords() -> List[str]:
    """Loads default keywords from a file in the script directory. Creates the file if it doesn't exist."""
    default_keywords_file = script_dir / 'default_keywords.txt'
    
    # Create the file if it doesn't exist
    if not default_keywords_file.exists():
        default_keywords_file.touch()
        print(f"Created default keywords file: {default_keywords_file}")
    
    try:
        with open(default_keywords_file, 'r', encoding='utf-8') as file:
            keywords = [line.strip() for line in file if line.strip()]
        
        if not keywords:
            print("Default keywords file is empty.")
        
        return keywords
    except Exception as e:
        print(f"Error reading default keywords file: {e}")
        return []

def main() -> None:
    db_path = input("Enter the path to the database file (press Enter to use the default 'statistics_image_metadata.db'): ").strip()
    if not db_path:
        db_path = os.path.join(script_dir, 'statistics_image_metadata.db')
    
    output_dir = os.path.join(script_dir, 'output_plots')
    prompt_text_output_path = os.path.join(script_dir, 'prompt_word_counts.txt')
    negative_prompt_text_output_path = os.path.join(script_dir, 'negative_prompt_word_counts.txt')
    parameter_text_output_path = os.path.join(script_dir, 'parameter_counts.txt')
    tfidf_text_output_path = os.path.join(script_dir, 'tfidf_analysis.txt')
    
    try:
        data_df = extract_data()
        logger_statistics.debug(f"Extracted {len(data_df)} records from the database.")
        logger_statistics.debug(f"Sample metadata: {data_df['metadata'].iloc[0] if not data_df.empty else 'No data'}")
        
        parsed_df = parse_metadata(data_df)
        logger_statistics.debug(f"Parsed {len(parsed_df)} records.")
        logger_statistics.debug(f"Sample parsed prompt: {parsed_df['prompt'].iloc[0] if not parsed_df.empty else 'No data'}")
        
        # User interaction for keywords and top models/samplers
        keyword_source = input("[Enter '1' to input keywords manually ] or [Enter '2' to load from a file] or [press Enter to use default keywords]: ").strip()
        if keyword_source == '1':
            keywords = input("Enter keywords (comma-separated): ").split(',')
            keywords = [keyword.strip() for keyword in keywords]
        elif keyword_source == '2':
            file_path = input("Enter the path to the keyword file: ").strip()
            keywords = load_keywords_from_file(file_path)
        else:
            print("Using default keywords.")
            keywords = load_default_keywords()

        top_models_n = int(input("Enter the number of top models to display (default is 3): ").strip() or "3")
        top_samplers_n = int(input("Enter the number of top samplers to display (default is 3): ").strip() or "3")
        
        # Analyze all data without specific keywords
        prompt_word_counts, negative_prompt_word_counts, parameter_counts = analyze_all(parsed_df)
        
        # TF-IDF analysis
        prompt_texts = parsed_df['prompt'].dropna().apply(preprocess_text)
        top_n_words, top_n_scores = tfidf_analysis(prompt_texts)
        
        # Plot TF-IDF analysis
        plot_tfidf_analysis(top_n_words, top_n_scores, output_dir)
        
        # Save TF-IDF analysis results
        save_tfidf_analysis_to_text(top_n_words, top_n_scores, tfidf_text_output_path)
        
        # Plot and save the analysis results
        plot_word_counts(prompt_word_counts, 'prompt words', output_dir)
        plot_word_counts(negative_prompt_word_counts, 'negative prompt words', output_dir)
        plot_parameter_counts(parameter_counts, output_dir)
        
        save_word_counts_to_text(prompt_word_counts, prompt_text_output_path, 'prompt words')
        save_word_counts_to_text(negative_prompt_word_counts, negative_prompt_text_output_path, 'negative prompt words')
        save_parameter_counts_to_text(parameter_counts, parameter_text_output_path)
        
        # If keywords were provided, perform additional analysis
        if keywords:
            keyword_prompt_counts = {keyword: 0 for keyword in keywords}
            keyword_model_counts = {keyword: Counter() for keyword in keywords}
            keyword_sampler_counts = {keyword: Counter() for keyword in keywords}
            
            for _, row in parsed_df.iterrows():
                prompt = preprocess_text(row['prompt'])
                for keyword in keywords:
                    if keyword in prompt:
                        keyword_prompt_counts[keyword] += 1
                        keyword_model_counts[keyword][row['Model']] += 1
                        keyword_sampler_counts[keyword][row['Sampler']] += 1
            
            sorted_keyword_counts = sorted(keyword_prompt_counts.items(), key=lambda x: x[1], reverse=True)
            
            with open(os.path.join(script_dir, 'keyword_analysis.txt'), 'w', encoding='utf-8') as file:
                for keyword, count in sorted_keyword_counts:
                    file.write(f"Keyword: {keyword}\n")
                    file.write(f"Count: {count}\n")
                    file.write("Top Models:\n")
                    for model, model_count in keyword_model_counts[keyword].most_common(top_models_n):
                        file.write(f"  {model}: {model_count}\n")
                    file.write("Top Samplers:\n")
                    for sampler, sampler_count in keyword_sampler_counts[keyword].most_common(top_samplers_n):
                        file.write(f"  {sampler}: {sampler_count}\n")
                    file.write("\n")
        
        print(f"Analysis complete. Results saved in {output_dir}")
    
    except Exception as e:
        logger_statistics.error(f"An error occurred during analysis: {e}")
        print(f"An error occurred during analysis: {e}")

if __name__ == "__main__":
    main()
