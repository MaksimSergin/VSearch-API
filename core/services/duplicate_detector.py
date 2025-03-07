# core/duplicate_detector.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import vstack
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")
russian_stopwords = stopwords.words("russian")

class VacancyDuplicateDetector:
    def __init__(self, threshold=0.85, initial_vacancies=None):
        self.threshold = threshold
        if initial_vacancies is None:
            initial_vacancies = []
        self.vacancies = initial_vacancies.copy()
        self.vectorizer = TfidfVectorizer(stop_words=russian_stopwords)
        if self.vacancies:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.vacancies)
        else:
            self.tfidf_matrix = None

    def is_duplicate(self, vacancy_text):
        if self.tfidf_matrix is None:
            return False, 0.0, None
        vacancy_vec = self.vectorizer.transform([vacancy_text])
        similarities = cosine_similarity(vacancy_vec, self.tfidf_matrix).flatten()
        max_similarity = similarities.max() if similarities.size > 0 else 0.0
        if max_similarity >= self.threshold:
            duplicate_index = similarities.argmax()
            duplicate_vacancy = self.vacancies[duplicate_index]
            return True, max_similarity, duplicate_vacancy
        return False, max_similarity, None

    def add_vacancy(self, vacancy_text):
        duplicate, similarity, _ = self.is_duplicate(vacancy_text)
        if duplicate:
            return False, similarity
        if self.tfidf_matrix is None:
            self.vacancies = [vacancy_text]
            self.tfidf_matrix = self.vectorizer.fit_transform(self.vacancies)
        else:
            self.vacancies.append(vacancy_text)
            new_vector = self.vectorizer.transform([vacancy_text])
            self.tfidf_matrix = vstack([self.tfidf_matrix, new_vector])
        return True, similarity
