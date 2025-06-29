#!/usr/bin/env python3
"""
Viral Mukbang Analysis
Advanced analysis to determine what makes mukbang videos go viral
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, classification_report, confusion_matrix
import xgboost as xgb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ViralMukbangAnalyzer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.viral_threshold = None
        self.feature_importance = None
        self.xgb_model = None
        
    def load_and_preprocess(self):
        """Load and preprocess the mukbang data"""
        print("🔄 Loading and preprocessing data...")
        
        # Load data
        self.df = pd.read_csv(self.data_path)
        
        # Convert duration to minutes
        self.df['duration_minutes'] = self.df['duration'] / 60
        
        # Clean view counts and engagement metrics
        self.df['view_count'] = pd.to_numeric(self.df['view_count'], errors='coerce')
        self.df['like_count'] = pd.to_numeric(self.df['like_count'], errors='coerce').fillna(0)
        self.df['comment_count'] = pd.to_numeric(self.df['comment_count'], errors='coerce').fillna(0)
        
        # Calculate engagement metrics (avoid division by zero)
        self.df['engagement_rate'] = np.where(
            self.df['view_count'] > 0,
            ((self.df['like_count'] + self.df['comment_count']) / self.df['view_count'] * 100),
            0
        )
        self.df['like_rate'] = np.where(
            self.df['view_count'] > 0,
            (self.df['like_count'] / self.df['view_count'] * 100),
            0
        )
        self.df['comment_rate'] = np.where(
            self.df['view_count'] > 0,
            (self.df['comment_count'] / self.df['view_count'] * 100),
            0
        )
        
        # Extract text features from titles
        self.df['title_length'] = self.df['title'].str.len()
        self.df['word_count'] = self.df['title'].str.split().str.len()
        self.df['has_emoji'] = self.df['title'].str.contains(r'[^\w\s]', regex=True)
        self.df['has_numbers'] = self.df['title'].str.contains(r'\d+', regex=True)
        self.df['has_caps'] = self.df['title'].str.contains(r'[A-Z]{2,}', regex=True)
        
        # Extract food-related features
        food_keywords = {
            'noodle': ['noodle', 'ramen', 'udon', 'soba', 'pasta'],
            'meat': ['chicken', 'beef', 'pork', 'meat', 'steak', 'burger'],
            'seafood': ['fish', 'shrimp', 'crab', 'lobster', 'sushi'],
            'spicy': ['spicy', 'hot', 'fire', 'chili', 'pepper'],
            'dessert': ['cake', 'ice cream', 'chocolate', 'sweet', 'dessert'],
            'fast_food': ['mcdonalds', 'kfc', 'burger king', 'pizza', 'taco'],
            'korean': ['korean', 'kimchi', 'bulgogi', 'bibimbap'],
            'japanese': ['japanese', 'sushi', 'ramen', 'tempura'],
            'chinese': ['chinese', 'dim sum', 'dumpling', 'wonton']
        }
        
        for category, keywords in food_keywords.items():
            pattern = '|'.join(keywords)
            self.df[f'has_{category}'] = self.df['title'].str.contains(pattern, case=False, na=False)
        
        # Create viral classification
        self.viral_threshold = self.df['view_count'].quantile(0.9)  # Top 10% as viral
        self.df['is_viral'] = self.df['view_count'] >= self.viral_threshold
        
        print(f"✅ Loaded {len(self.df)} videos")
        print(f"📊 Viral threshold: {self.viral_threshold:,.0f} views")
        print(f"🔥 Viral videos: {self.df['is_viral'].sum()} ({self.df['is_viral'].mean()*100:.1f}%)")
        
        return self.df
    
    def analyze_viral_factors(self):
        """Analyze what factors contribute to virality"""
        print("\n🔍 Analyzing viral factors...")
        
        # 1. Duration Analysis
        print("\n📏 Duration Analysis:")
        viral_duration = self.df[self.df['is_viral']]['duration_minutes'].mean()
        non_viral_duration = self.df[~self.df['is_viral']]['duration_minutes'].mean()
        print(f"   Viral videos: {viral_duration:.1f} minutes")
        print(f"   Non-viral videos: {non_viral_duration:.1f} minutes")
        print(f"   Difference: {viral_duration - non_viral_duration:.1f} minutes")
        
        # 2. Engagement Analysis
        print("\n💬 Engagement Analysis:")
        viral_engagement = self.df[self.df['is_viral']]['engagement_rate'].mean()
        non_viral_engagement = self.df[~self.df['is_viral']]['engagement_rate'].mean()
        print(f"   Viral videos: {viral_engagement:.2f}% engagement")
        print(f"   Non-viral videos: {non_viral_engagement:.2f}% engagement")
        print(f"   Difference: {viral_engagement - non_viral_engagement:.2f}%")
        
        # 3. Title Analysis
        print("\n📝 Title Analysis:")
        viral_title_length = self.df[self.df['is_viral']]['title_length'].mean()
        non_viral_title_length = self.df[~self.df['is_viral']]['title_length'].mean()
        print(f"   Viral videos: {viral_title_length:.0f} characters")
        print(f"   Non-viral videos: {non_viral_title_length:.0f} characters")
        
        # 4. Food Category Analysis
        print("\n🍽️ Food Category Analysis:")
        food_features = [col for col in self.df.columns if col.startswith('has_')]
        food_analysis = []
        
        for feature in food_features:
            viral_rate = self.df[self.df['is_viral']][feature].mean()
            non_viral_rate = self.df[~self.df['is_viral']][feature].mean()
            food_analysis.append({
                'category': feature.replace('has_', ''),
                'viral_rate': viral_rate,
                'non_viral_rate': non_viral_rate,
                'difference': viral_rate - non_viral_rate
            })
        
        food_df = pd.DataFrame(food_analysis)
        food_df = food_df.sort_values('difference', ascending=False)
        
        print("   Top viral food categories:")
        for _, row in food_df.head(5).iterrows():
            print(f"   - {row['category']}: {row['difference']*100:.1f}% higher in viral videos")
        
        return food_df
    
    def build_xgboost_model(self):
        """Build an XGBoost model to predict virality"""
        print("\n🤖 Building XGBoost viral prediction model...")
        
        # Prepare features
        feature_columns = [
            'duration_minutes', 'title_length', 'word_count', 'has_emoji', 
            'has_numbers', 'has_caps', 'engagement_rate', 'like_rate', 'comment_rate'
        ] + [col for col in self.df.columns if col.startswith('has_')]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for col in feature_columns:
            if col not in seen:
                seen.add(col)
                unique_features.append(col)
        
        feature_columns = unique_features
        
        # Remove rows with missing values
        model_df = self.df[feature_columns + ['is_viral']].dropna()
        
        if len(model_df) < 10:
            print("   ⚠️  Not enough data for reliable model training")
            return None, None
        
        X = model_df[feature_columns]
        y = model_df['is_viral'].astype(int)  # XGBoost needs integer labels
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Train XGBoost model
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.xgb_model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.xgb_model.predict(X_test)
        y_pred_proba = self.xgb_model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = self.xgb_model.score(X_test, y_test)
        mse = mean_squared_error(y_test, y_pred_proba)
        
        print(f"   Model Accuracy: {accuracy:.3f}")
        print(f"   Mean Squared Error: {mse:.3f}")
        
        # Classification report
        print("\n   Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Non-Viral', 'Viral']))
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': feature_columns,
            'importance': self.xgb_model.feature_importances_
        }).sort_values('importance', ascending=False)

        # Save feature importance to CSV for dashboard
        self.feature_importance.to_csv('output/xgboost_feature_importance.csv', index=False)

        print("\n   Top 10 most important features for virality:")
        for _, row in self.feature_importance.head(10).iterrows():
            print(f"   - {row['feature']}: {row['importance']:.3f}")
        
        return self.xgb_model, self.feature_importance
    
    def create_viral_insights_report(self):
        """Create a comprehensive viral insights report"""
        print("\n📊 Creating viral insights report...")
        
        # Calculate viral success factors
        viral_videos = self.df[self.df['is_viral']]
        non_viral_videos = self.df[~self.df['is_viral']]
        
        insights = {
            'total_videos': len(self.df),
            'viral_videos': len(viral_videos),
            'viral_percentage': len(viral_videos) / len(self.df) * 100,
            'viral_threshold': self.viral_threshold,
            
            # Duration insights
            'optimal_duration': viral_videos['duration_minutes'].median(),
            'duration_range': f"{viral_videos['duration_minutes'].quantile(0.25):.1f}-{viral_videos['duration_minutes'].quantile(0.75):.1f} minutes",
            
            # Engagement insights
            'min_engagement_viral': viral_videos['engagement_rate'].min(),
            'avg_engagement_viral': viral_videos['engagement_rate'].mean(),
            
            # Title insights
            'optimal_title_length': viral_videos['title_length'].median(),
            'emoji_usage_viral': viral_videos['has_emoji'].mean() * 100,
            'caps_usage_viral': viral_videos['has_caps'].mean() * 100,
            
            # Content insights
            'top_food_categories': self.get_top_food_categories(viral_videos),
            'creator_insights': self.get_creator_insights(viral_videos)
        }
        
        return insights
    
    def get_top_food_categories(self, viral_videos):
        """Get top food categories in viral videos"""
        food_features = [col for col in viral_videos.columns if col.startswith('has_')]
        food_stats = []
        
        for feature in food_features:
            category = feature.replace('has_', '')
            usage_rate = viral_videos[feature].mean() * 100
            food_stats.append({'category': category, 'usage_rate': usage_rate})
        
        return pd.DataFrame(food_stats).sort_values('usage_rate', ascending=False).head(5)
    
    def get_creator_insights(self, viral_videos):
        """Get insights about creators of viral videos"""
        creator_stats = viral_videos.groupby('creator_name').agg({
            'video_id': 'count',
            'view_count': 'mean',
            'engagement_rate': 'mean'
        }).reset_index()
        
        creator_stats.columns = ['Creator', 'Viral_Videos', 'Avg_Views', 'Avg_Engagement']
        return creator_stats.sort_values('Viral_Videos', ascending=False).head(5)
    
    def generate_recommendations(self):
        """Generate actionable recommendations for creating viral mukbang content"""
        print("\n💡 Generating viral recommendations...")
        
        insights = self.create_viral_insights_report()
        
        recommendations = {
            'duration': {
                'optimal': f"{insights['optimal_duration']:.1f} minutes",
                'range': insights['duration_range'],
                'tip': "Aim for the sweet spot duration that keeps viewers engaged without losing their attention"
            },
            'engagement': {
                'target': f"{insights['min_engagement_viral']:.2f}%",
                'tip': "Focus on creating content that encourages likes and comments"
            },
            'titles': {
                'length': f"{insights['optimal_title_length']:.0f} characters",
                'emoji': f"{insights['emoji_usage_viral']:.1f}% of viral videos use emojis",
                'caps': f"{insights['caps_usage_viral']:.1f}% of viral videos use CAPS",
                'tip': "Use attention-grabbing titles with emojis and strategic capitalization"
            },
            'content': {
                'top_foods': insights['top_food_categories']['category'].tolist(),
                'tip': "Focus on popular food categories that consistently perform well"
            }
        }
        
        return recommendations

def main():
    """Main analysis function"""
    print("🍜 VIRAL MUKBANG ANALYSIS (XGBoost Edition)")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = ViralMukbangAnalyzer('data/youtube_mukbang_20250621_193144.csv')
    
    # Load and preprocess data
    df = analyzer.load_and_preprocess()
    
    # Analyze viral factors
    food_analysis = analyzer.analyze_viral_factors()
    
    # Build XGBoost prediction model
    model, feature_importance = analyzer.build_xgboost_model()
    
    # Generate insights and recommendations
    insights = analyzer.create_viral_insights_report()
    recommendations = analyzer.generate_recommendations()
    
    # Print comprehensive report
    print("\n" + "=" * 50)
    print("📈 VIRAL MUKBANG INSIGHTS REPORT (XGBoost)")
    print("=" * 50)
    
    print(f"\n📊 Dataset Overview:")
    print(f"   Total videos analyzed: {insights['total_videos']}")
    print(f"   Viral videos: {insights['viral_videos']} ({insights['viral_percentage']:.1f}%)")
    print(f"   Viral threshold: {insights['viral_threshold']:,.0f} views")
    
    print(f"\n🎯 Key Viral Factors:")
    print(f"   Optimal duration: {recommendations['duration']['optimal']}")
    print(f"   Duration range: {recommendations['duration']['range']}")
    print(f"   Target engagement: {recommendations['engagement']['target']}")
    print(f"   Optimal title length: {recommendations['titles']['length']} characters")
    
    print(f"\n🍽️ Top Viral Food Categories:")
    for _, row in insights['top_food_categories'].iterrows():
        print(f"   - {row['category'].title()}: {row['usage_rate']:.1f}% of viral videos")
    
    print(f"\n👤 Top Viral Creators:")
    for _, row in insights['creator_insights'].iterrows():
        print(f"   - {row['Creator']}: {row['Viral_Videos']} viral videos")
    
    print(f"\n💡 Actionable Recommendations:")
    print(f"   1. {recommendations['duration']['tip']}")
    print(f"   2. {recommendations['engagement']['tip']}")
    print(f"   3. {recommendations['titles']['tip']}")
    print(f"   4. {recommendations['content']['tip']}")
    
    if feature_importance is not None:
        print(f"\n🔮 XGBoost Feature Importance:")
        print(f"   Top 5 features for virality:")
        for _, row in feature_importance.head(5).iterrows():
            print(f"   - {row['feature']}: {row['importance']:.3f}")
    
    print("\n" + "=" * 50)
    print("✅ Analysis Complete!")
    print("=" * 50)
    
    return analyzer, insights, recommendations, feature_importance

if __name__ == "__main__":
    analyzer, insights, recommendations, feature_importance = main() 