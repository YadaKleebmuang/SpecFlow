from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import sys
import os

# Add the project root to sys.path to allow importing from the app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from app.services.recommendation.spec_recommender import SpecRecommender
from app.rasa.actions.flex import generate_spec_flex_message

class ActionRecommendPC(Action):

    def name(self) -> Text:
        return "action_recommend_pc"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        budget = tracker.get_slot("budget")
        usage = tracker.get_slot("usage")

        recommender = SpecRecommender()
        result = recommender.get_recommendation(budget, usage)

        if isinstance(result, dict) and result.get("status") == "success":
            # Generate Flex Message payload
            flex_payload = generate_spec_flex_message(
                total_price=result["total_price"], 
                components=result["components"],
                usage=usage
            )
            # Send text as fallback for unsupported clients, and flex for LINE
            dispatcher.utter_message(
                text=result["text"],
                custom=flex_payload
            )
        elif isinstance(result, dict):
            dispatcher.utter_message(text=result.get("text", "เกิดข้อผิดพลาดในการคำนวณสเปคครับ"))
        else:
            # Fallback if result is just a string
            dispatcher.utter_message(text=str(result))

        return []
