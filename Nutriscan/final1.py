import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
from difflib import SequenceMatcher
import json

# ===============================
# CONFIGURATION
# ===============================
EXACT_MATCH_THRESHOLD = 0.95  # Very high for exact matches
FUZZY_MATCH_THRESHOLD = 0.80  # High threshold for fuzzy matches
TFIDF_THRESHOLD = 0.50  # Medium threshold for TF-IDF
CACHE_SIZE = 1000

# ===============================
# E-NUMBER MAPPING
# ===============================
E_NUMBER_MAP = {
    'e330': 'citric acid',
    'e500': 'sodium carbonate',
    'e501': 'potassium carbonate',
    'e508': 'potassium chloride',
    'e170': 'calcium carbonate',
    'e412': 'guar gum',
    'e452': 'sodium phosphate',
    'e100': 'curcumin',
    'e627': 'disodium guanylate',
    'e631': 'disodium inosinate',
    'e551': 'silicon dioxide',
    'e621': 'monosodium glutamate',
    'e322': 'lecithin',
    'e471': 'mono and diglycerides',
    'e407': 'carrageenan',
    'e410': 'locust bean gum',
    'e415': 'xanthan gum',
    'e150': 'caramel',
    'e202': 'potassium sorbate',
    'e211': 'sodium benzoate',
    'e223': 'sodium metabisulphite',
    'e300': 'ascorbic acid',
    'e503': 'ammonium carbonate',
}

# ===============================
# INDIAN INGREDIENT MAPPING
# ===============================
INDIAN_INGREDIENT_MAP = {
    'maida': 'refined wheat flour',
    'atta': 'whole wheat flour',
    'besan': 'gram flour',
    'hing': 'asafoetida',
    'jeera': 'cumin',
    'haldi': 'turmeric',
    'dhaniya': 'coriander',
    'elaichi': 'cardamom',
    'dalchini': 'cinnamon',
    'kalonji': 'nigella seeds',
    'methi': 'fenugreek',
    'ajwain': 'carom seeds',
    'til': 'sesame',
    'kaju': 'cashew',
    'badam': 'almond',
    'pista': 'pistachio',
    'khoya': 'milk solids',
    'paneer': 'cottage cheese',
}

# ===============================
# IMPROVED FOOD ANALYZER
# ===============================
class FoodAnalyzer:
    def __init__(self, csv_path="food_ingridients.csv"):
        """Initialize the food analyzer with dataset and ML models."""
        self.df = pd.read_csv(csv_path)
        self.df.fillna("", inplace=True)
        
        # Preprocess dataset
        self.df['Ingredient_LC'] = self.df['Food_Ingredient'].str.lower().str.strip()
        
        # Create variations for better matching
        self.create_ingredient_variations()
        
        # Setup TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),
            min_df=1,
            max_features=5000
        )
        self.ingredient_vectors = self.vectorizer.fit_transform(
            self.df['Food_Ingredient']
        )
        
        print("✅ Food Analyzer initialized successfully!")
        print(f"📊 Loaded {len(self.df)} ingredients from database")

    def create_ingredient_variations(self):
        """Create common variations of ingredient names for better matching."""
        self.ingredient_map = {}
        
        for idx, row in self.df.iterrows():
            ingredient = row['Ingredient_LC']
            
            # Store original
            self.ingredient_map[ingredient] = idx
            
            # Store without common words
            clean_name = re.sub(r'\b(powder|extract|natural|artificial|added|permitted)\b', '', ingredient).strip()
            if clean_name and clean_name != ingredient:
                if clean_name not in self.ingredient_map:
                    self.ingredient_map[clean_name] = idx

    # ===============================
    # TEXT CLEANING - MORE CONSERVATIVE
    # ===============================
    def clean_ingredient_text(self, raw_text):
        """Conservative OCR text preprocessing - preserve actual ingredients."""
        text = raw_text.lower()
        
        # Remove ONLY packaging info sections (not individual ingredients)
        removal_patterns = [
            r"allergen\s+(advice|information)[:\s].*",
            r"may contain traces of.*",
            r"storage instructions[:\s].*",
            r"best before[:\s].*",
            r"contains added permitted",
        ]
        for pattern in removal_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
        
        # Replace E-numbers with actual names
        for e_code, ingredient_name in E_NUMBER_MAP.items():
            text = re.sub(rf'\b{e_code}\b', ingredient_name, text, flags=re.IGNORECASE)
        
        # Replace Indian names with English equivalents
        for indian, english in INDIAN_INGREDIENT_MAP.items():
            text = re.sub(rf'\b{indian}\b', english, text, flags=re.IGNORECASE)
        
        # Remove content in brackets/parentheses but keep the word before it
        text = re.sub(r'\s*[\[\(].*?[\]\)]', '', text)
        
        # Remove descriptive phrases like "as thickener", "as preservative"
        text = re.sub(r'\s+as\s+(thickener|stabilizer|emulsifier|preservative|colour|flavor|acidity regulator|raising agent|anticaking agent|mineral|vitamin)', '', text, flags=re.IGNORECASE)
        
        # Replace common separators with commas
        text = re.sub(r'[;|\n\t&]', ',', text)
        
        # Remove numbers at the start of ingredients (e.g., "1. Sugar" -> "Sugar")
        text = re.sub(r'\b\d+\.\s*', '', text)
        
        # Clean up colons used in labels
        text = re.sub(r'(ingredients?|contains?|noodles?|tastemaker|seasoning)\s*:', ',', text, flags=re.IGNORECASE)
        
        return text

    def extract_ingredients_list(self, cleaned_text):
        """Extract individual ingredients from cleaned text."""
        # Split by commas
        raw_ingredients = [i.strip() for i in cleaned_text.split(',') if i.strip()]
        
        cleaned_ingredients = []
        
        for ing in raw_ingredients:
            # Skip if too short (likely noise)
            if len(ing) < 3:
                continue
            
            # Skip common non-ingredient words
            skip_words = ['ingredients', 'contains', 'allergen', 'advice', 'information', 
                         'may contain', 'traces', 'added permitted', 'natural identical',
                         'flavouring substances', 'natural', 'artificial']
            
            if any(skip in ing.lower() for skip in skip_words) and len(ing.split()) < 3:
                continue
            
            # Remove leading/trailing special characters
            ing = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', ing, flags=re.IGNORECASE)
            
            # Skip if only numbers or special characters remain
            if not re.search(r'[a-z]', ing, flags=re.IGNORECASE):
                continue
            
            cleaned_ingredients.append(ing)
        
        return cleaned_ingredients

    # ===============================
    # SIMILARITY MATCHING
    # ===============================
    def calculate_similarity(self, str1, str2):
        """Calculate similarity between two strings."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    @lru_cache(maxsize=CACHE_SIZE)
    def find_best_match(self, ingredient):
        """Find best matching ingredient from database using multiple methods."""
        ing_lc = ingredient.lower().strip()
        
        # Method 1: Exact match
        if ing_lc in self.ingredient_map:
            idx = self.ingredient_map[ing_lc]
            row = self.df.iloc[idx]
            return {
                'ingredient': ingredient,
                'matched_as': row['Food_Ingredient'],
                'score': float(row['Nutrition_Score']),
                'label': row['Health_Label'],
                'remark': row['Remarks'],
                'category': row['Category'],
                'confidence': 1.0,
                'method': 'exact_match'
            }
        
        # Method 2: Fuzzy string matching
        best_fuzzy_score = 0
        best_fuzzy_idx = None
        
        for db_ing, idx in self.ingredient_map.items():
            similarity = self.calculate_similarity(ing_lc, db_ing)
            if similarity > best_fuzzy_score:
                best_fuzzy_score = similarity
                best_fuzzy_idx = idx
        
        if best_fuzzy_score >= FUZZY_MATCH_THRESHOLD:
            row = self.df.iloc[best_fuzzy_idx]
            return {
                'ingredient': ingredient,
                'matched_as': row['Food_Ingredient'],
                'score': float(row['Nutrition_Score']),
                'label': row['Health_Label'],
                'remark': row['Remarks'],
                'category': row['Category'],
                'confidence': best_fuzzy_score,
                'method': f'fuzzy_match ({best_fuzzy_score:.2f})'
            }
        
        # Method 3: TF-IDF Similarity (only if fuzzy didn't work well)
        try:
            input_vec = self.vectorizer.transform([ing_lc])
            sims = cosine_similarity(input_vec, self.ingredient_vectors)
            best_tfidf_idx = sims.argmax()
            best_tfidf_score = sims[0][best_tfidf_idx]
            
            if best_tfidf_score > TFIDF_THRESHOLD:
                row = self.df.iloc[best_tfidf_idx]
                return {
                    'ingredient': ingredient,
                    'matched_as': row['Food_Ingredient'],
                    'score': float(row['Nutrition_Score']),
                    'label': row['Health_Label'],
                    'remark': row['Remarks'],
                    'category': row['Category'],
                    'confidence': best_tfidf_score,
                    'method': f'tfidf_match ({best_tfidf_score:.2f})'
                }
        except:
            pass
        
        # Method 4: Partial word matching for compound ingredients
        words_in_ingredient = set(ing_lc.split())
        best_partial_score = 0
        best_partial_idx = None
        
        for db_ing, idx in self.ingredient_map.items():
            words_in_db = set(db_ing.split())
            
            # Calculate word overlap
            if words_in_ingredient and words_in_db:
                overlap = len(words_in_ingredient & words_in_db)
                total_words = len(words_in_ingredient | words_in_db)
                partial_score = overlap / total_words
                
                if partial_score > best_partial_score:
                    best_partial_score = partial_score
                    best_partial_idx = idx
        
        if best_partial_score >= 0.6:  # At least 60% word overlap
            row = self.df.iloc[best_partial_idx]
            return {
                'ingredient': ingredient,
                'matched_as': row['Food_Ingredient'],
                'score': float(row['Nutrition_Score']),
                'label': row['Health_Label'],
                'remark': row['Remarks'],
                'category': row['Category'],
                'confidence': best_partial_score,
                'method': f'partial_match ({best_partial_score:.2f})'
            }
        
        # No match found - return as unmatched
        return None

    # ===============================
    # FALLBACK FOR UNMATCHED INGREDIENTS
    # ===============================
    def analyze_unknown_ingredient(self, ingredient):
        """Analyze ingredient that couldn't be matched to database."""
        ing = ingredient.lower()
        
        # Very harmful
        if any(x in ing for x in ["trans fat", "partially hydrogenated", "hydrogenated oil"]):
            return {
                'ingredient': ingredient,
                'matched_as': 'Not in Database',
                'score': 1.0,
                'label': 'Avoid',
                'remark': '❌ Trans fats detected - Highly harmful to heart health',
                'category': 'Fats & Oils',
                'confidence': 0.8,
                'method': 'keyword_detection'
            }
        
        # Harmful additives
        if any(x in ing for x in ["artificial color", "artificial colour", "tartrazine", "sunset yellow"]):
            return {
                'ingredient': ingredient,
                'matched_as': 'Not in Database',
                'score': 2.0,
                'label': 'Avoid',
                'remark': '⚠️ Artificial colorant - May cause allergic reactions',
                'category': 'Additives',
                'confidence': 0.75,
                'method': 'keyword_detection'
            }
        
        # Preservatives
        if any(x in ing for x in ["preservative", "benzoate", "sorbate", "sulfite", "nitrite", "nitrate"]):
            return {
                'ingredient': ingredient,
                'matched_as': 'Not in Database',
                'score': 3.0,
                'label': 'Caution',
                'remark': '⚠️ Chemical preservative - Consume in moderation',
                'category': 'Preservatives',
                'confidence': 0.7,
                'method': 'keyword_detection'
            }
        
        # Flavor enhancers
        if any(x in ing for x in ["msg", "monosodium glutamate", "disodium", "flavor enhancer"]):
            return {
                'ingredient': ingredient,
                'matched_as': 'Not in Database',
                'score': 3.0,
                'label': 'Caution',
                'remark': '⚠️ Flavor enhancer - May cause sensitivity in some people',
                'category': 'Flavor Enhancers',
                'confidence': 0.7,
                'method': 'keyword_detection'
            }
        
        # High sugar
        if any(x in ing for x in ["sugar", "syrup", "high fructose", "corn syrup"]):
            return {
                'ingredient': ingredient,
                'matched_as': 'Not in Database',
                'score': 3.5,
                'label': 'Caution',
                'remark': '🍬 High sugar content - Limit consumption',
                'category': 'Sweeteners',
                'confidence': 0.75,
                'method': 'keyword_detection'
            }
        
        # Healthy indicators
        if any(x in ing for x in ["vitamin", "mineral", "probiotic", "lactobacillus", "bifidobacterium"]):
            return {
                'ingredient': ingredient,
                'matched_as': 'Not in Database',
                'score': 8.0,
                'label': 'Healthy',
                'remark': '✅ Beneficial nutrient or probiotic',
                'category': 'Nutrients',
                'confidence': 0.8,
                'method': 'keyword_detection'
            }
        
        if any(x in ing for x in ["whole grain", "whole wheat", "oats", "quinoa", "brown rice"]):
            return {
                'ingredient': ingredient,
                'matched_as': 'Not in Database',
                'score': 8.5,
                'label': 'Healthy',
                'remark': '✅ Whole grain - Good source of fiber',
                'category': 'Grains',
                'confidence': 0.8,
                'method': 'keyword_detection'
            }
        
        # Return as unknown with neutral score
        return {
            'ingredient': ingredient,
            'matched_as': 'Not in Database',
            'score': 5.0,
            'label': 'Unknown',
            'remark': '❓ Ingredient not found in database - Neutral impact assumed',
            'category': 'Unknown',
            'confidence': 0.0,
            'method': 'not_found'
        }

    # ===============================
    # MAIN ANALYSIS FUNCTION
    # ===============================
    def analyze_product(self, raw_text, product_name="Unknown Product"):
        """Analyze complete food product and return comprehensive health report."""
        
        # Clean text
        cleaned = self.clean_ingredient_text(raw_text)
        ingredients_list = self.extract_ingredients_list(cleaned)
        
        if not ingredients_list:
            return {
                'error': 'No ingredients found in text',
                'product_name': product_name,
                'final_score': 0,
                'total_ingredients': 0,
                'recommendation': 'Unable to analyze - No ingredients detected',
                'ingredients': [],
                'flags': {
                    'has_harmful': False,
                    'has_caution': False
                }
            }
        
        # Analyze each ingredient
        ingredient_results = []
        matched_count = 0
        unmatched_count = 0
        total_score = 0
        found_avoid = False
        found_caution = False
        
        for ing in ingredients_list:
            # Try to find match in database
            result = self.find_best_match(ing)
            
            # If no match found, analyze as unknown
            if result is None:
                result = self.analyze_unknown_ingredient(ing)
                unmatched_count += 1
            else:
                matched_count += 1
            
            ingredient_results.append(result)
            
            # Track scores and flags
            total_score += result['score']
            label = result['label'].lower()
            
            if 'avoid' in label:
                found_avoid = True
            elif 'caution' in label:
                found_caution = True
        
        # Calculate final score (simple average)
        final_score = total_score / len(ingredient_results) if ingredient_results else 5.0
        final_score = round(final_score, 2)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(final_score, found_avoid, found_caution, matched_count, len(ingredient_results))
        
        # Prepare output
        result = {
            'product_name': product_name,
            'final_score': final_score,
            'total_ingredients': len(ingredient_results),
            'matched_ingredients': matched_count,
            'unmatched_ingredients': unmatched_count,
            'recommendation': recommendation,
            'ingredients': ingredient_results,
            'flags': {
                'has_harmful': found_avoid,
                'has_caution': found_caution
            }
        }
        
        return result

    # ===============================
    # RECOMMENDATION GENERATOR
    # ===============================
    def _generate_recommendation(self, score, has_avoid, has_caution, matched, total):
        """Generate health recommendation based on score."""
        match_rate = (matched / total * 100) if total > 0 else 0
        
        recommendation = ""
        
        if score >= 8:
            recommendation = "✅ Excellent Choice! This product is healthy and nutritious."
        elif score >= 6.5:
            recommendation = "👍 Good Choice! Generally safe but consume in moderation."
        elif score >= 5:
            recommendation = "⚠️ Moderate! Contains some ingredients to be cautious about."
        elif score >= 3:
            recommendation = "🚨 Poor Choice! Contains multiple harmful ingredients. Limit consumption."
        else:
            recommendation = "❌ Avoid! This product contains highly harmful ingredients."
        
        if has_avoid:
            recommendation += " Contains harmful ingredients."
        elif has_caution:
            recommendation += " Contains ingredients requiring caution."
        
        return recommendation

    # ===============================
    # DISPLAY RESULTS
    # ===============================
    def print_report(self, result):
        """Print formatted analysis report."""
        print("\n" + "="*70)
        print("🔬 FOOD PRODUCT HEALTH ANALYSIS REPORT")
        print("="*70)
        print(f"📦 Product: {result['product_name']}")
        print(f"🎯 Health Score: {result['final_score']}/10")
        print(f"📊 Total Ingredients: {result['total_ingredients']}")
        print(f"Matched in Database: {result['matched_ingredients']}")
        print(f"Not in Database: {result['unmatched_ingredients']}")
        print(f"💡 Recommendation: {result['recommendation']}")
        print("="*70)
        
        print("\n📋 INGREDIENT BREAKDOWN:\n")
        for i, ing_data in enumerate(result['ingredients'], 1):
            label_lower = ing_data['label'].lower()
            #emoji = "✅" if "healthy" in label_lower else "⚠️" if "caution" in label_lower else "❌" if "avoid" in label_lower else "❓"
            
            print(f"{i}. {ing_data['ingredient'].title()}")
            print(f"   ├─ Matched As: {ing_data['matched_as']}")
            print(f"   ├─ Category: {ing_data.get('category', 'N/A')}")
            print(f"   ├─ Health Score: {ing_data['score']}/10")
            print(f"   ├─ Label: {ing_data['label']}")
            print(f"   ├─ Confidence: {ing_data['confidence']:.2%}")
            print(f"   ├─ Method: {ing_data['method']}")
            print(f"   └─ {ing_data['remark']}\n")
        
        print("="*70)

    # ===============================
    # EXPORT TO JSON
    # ===============================
    def export_json(self, result, filename="analysis_result.json"):
        """Export result as JSON for mobile app consumption."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Results exported to {filename}")


# EXAMPLE USAGE

if __name__ == "__main__":
    # Initialize analyzer
    analyzer = FoodAnalyzer("food_ingridients.csv")
    
    # Example: Yakult
    print("\n📱 ANALYZING: YAKULT")
    ocr_text = """Water, Sugar, Skimmed Milk Powder, Glucose, Probiotic-Lactobacillus casei strain Shirota, 
    CONTAINS NATURAL & NATURAL IDENTICAL FLAVOURS
    ALLERGEN INFORMATION: CONTAINS MILK PRODUCTS."""
    
    result = analyzer.analyze_product(ocr_text, "Yakult")
    analyzer.print_report(result)
    
    # Export for mobile app
    analyzer.export_json(result, "yakult_analysis.json")
    
    print("\n✅ Analysis complete! Ready for mobile integration.")