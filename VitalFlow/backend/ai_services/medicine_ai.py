"""
AI-powered medicine and equipment recommendations.
Uses OpenAI GPT or Google Gemini with intelligent fallbacks.
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, PatientStatus
from .prompts import MEDICINE_RECOMMENDATION_PROMPT, MEDICINE_RECOMMENDATION_SIMPLE, format_prompt


class MedicineAI:
    """
    AI-powered medicine and equipment recommendation service.
    Supports OpenAI GPT and Google Gemini with rule-based fallback.
    """
    
    def __init__(self):
        """Initialize AI service with API keys from environment."""
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Cache for recommendations to avoid repeated API calls
        self._cache: Dict[str, Dict] = {}
    
    def get_preparation_checklist(self, patient: Patient) -> Dict:
        """
        Generate preparation checklist for nursing staff based on patient condition.
        
        Args:
            patient: Patient object with diagnosis, vitals, etc.
            
        Returns:
            Dict with equipment, medications, urgency, and instructions
        """
        # Check cache first
        cache_key = f"{patient.diagnosis}_{patient.status}_{patient.spo2}_{patient.heart_rate}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Build prompt
        prompt = format_prompt(
            MEDICINE_RECOMMENDATION_PROMPT,
            patient_name=patient.name,
            age=patient.age,
            diagnosis=patient.diagnosis or "Unknown",
            status=patient.status.value if isinstance(patient.status, PatientStatus) else patient.status,
            spo2=patient.spo2,
            heart_rate=patient.heart_rate,
            blood_pressure=getattr(patient, 'blood_pressure', '120/80'),
            temperature=getattr(patient, 'temperature', 98.6),
            bed_id=patient.bed_id or "Pending",
            priority=getattr(patient, 'priority', 3)
        )
        
        # Try OpenAI first, then Gemini, then fallback
        result = self._call_openai(prompt)
        if not result:
            result = self._call_gemini(prompt)
        if not result:
            result = self._fallback_recommendation(patient)
        
        # Cache the result
        self._cache[cache_key] = result
        
        return result
    
    def _call_openai(self, prompt: str) -> Optional[Dict]:
        """
        Call OpenAI API for recommendation.
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            Dict with recommendation or None if API fails
        """
        if not self.openai_key:
            return None
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a medical AI assistant. Always respond with valid JSON only, no markdown formatting."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Clean up response (remove markdown code blocks if present)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            return json.loads(content)
            
        except ImportError:
            print("OpenAI package not installed. Run: pip install openai")
            return None
        except json.JSONDecodeError as e:
            print(f"OpenAI response JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def _call_gemini(self, prompt: str) -> Optional[Dict]:
        """
        Call Google Gemini API for recommendation.
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            Dict with recommendation or None if API fails
        """
        if not self.gemini_key:
            return None
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content(
                f"Respond with valid JSON only, no markdown. {prompt}"
            )
            
            content = response.text.strip()
            
            # Clean up response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            return json.loads(content)
            
        except ImportError:
            print("Google Generative AI package not installed. Run: pip install google-generativeai")
            return None
        except json.JSONDecodeError as e:
            print(f"Gemini response JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None
    
    def _fallback_recommendation(self, patient: Patient) -> Dict:
        """
        Rule-based fallback when AI APIs are unavailable.
        Uses medical knowledge base for common conditions.
        
        Args:
            patient: Patient object
            
        Returns:
            Dict with equipment, medications, urgency, etc.
        """
        recommendations = {
            "equipment": ["Vital signs monitor", "Pulse oximeter"],
            "medications": [],
            "urgency": "MEDIUM",
            "special_instructions": "",
            "monitoring_frequency": "Every 4 hours",
            "warning_signs": ["Sudden change in vitals", "Loss of consciousness"]
        }
        
        status = patient.status.value if isinstance(patient.status, PatientStatus) else patient.status
        diagnosis_lower = (patient.diagnosis or "").lower()
        
        # ========== CRITICAL PATIENTS ==========
        if status == "Critical" or patient.spo2 < 85:
            recommendations["equipment"].extend([
                "Defibrillator",
                "Emergency crash cart",
                "Oxygen mask with reservoir",
                "Intubation kit",
                "IV stand with infusion pump",
                "ECG machine (12-lead)",
                "Suction device"
            ])
            recommendations["medications"].extend([
                "Epinephrine 1mg IV/IM",
                "Atropine 0.5mg IV",
                "Amiodarone 150mg IV",
                "Normal Saline 1L",
                "Sodium Bicarbonate 50mEq"
            ])
            recommendations["urgency"] = "HIGH"
            recommendations["monitoring_frequency"] = "Continuous"
            recommendations["special_instructions"] = (
                "Prepare for possible cardiac arrest. "
                "Have crash cart at bedside. "
                "Notify senior physician immediately. "
                "Ensure airway management equipment ready."
            )
            recommendations["warning_signs"] = [
                "Cardiac arrest",
                "Respiratory failure",
                "SpO2 below 80%",
                "Loss of consciousness",
                "Ventricular arrhythmias"
            ]
        
        # ========== LOW SpO2 (HYPOXIA) ==========
        elif patient.spo2 < 90:
            recommendations["equipment"].extend([
                "Oxygen concentrator",
                "Non-rebreather mask",
                "Nasal cannula (backup)",
                "Suction device",
                "Bag-valve mask"
            ])
            recommendations["medications"].extend([
                "Bronchodilator inhaler (Salbutamol)",
                "Dexamethasone 4mg IV",
                "Nebulizer solution"
            ])
            recommendations["urgency"] = "HIGH"
            recommendations["monitoring_frequency"] = "Every 30 minutes"
            recommendations["special_instructions"] = (
                "Start oxygen therapy immediately. "
                "Position patient upright (Fowler's position). "
                "Prepare for possible intubation if SpO2 doesn't improve."
            )
            recommendations["warning_signs"].extend([
                "SpO2 dropping below 85%",
                "Increased work of breathing",
                "Cyanosis",
                "Altered mental status"
            ])
        
        # ========== ABNORMAL HEART RATE ==========
        if patient.heart_rate > 120 or patient.heart_rate < 50:
            recommendations["equipment"].append("ECG machine (12-lead)")
            recommendations["equipment"].append("Defibrillator (standby)")
            
            if patient.heart_rate > 140:
                recommendations["medications"].extend([
                    "Metoprolol 5mg IV",
                    "Adenosine 6mg IV (if SVT)"
                ])
            elif patient.heart_rate < 50:
                recommendations["medications"].extend([
                    "Atropine 0.5mg IV",
                    "Transcutaneous pacing ready"
                ])
            
            recommendations["urgency"] = "HIGH"
            recommendations["warning_signs"].extend([
                "Ventricular tachycardia",
                "Complete heart block",
                "Syncope"
            ])
        
        # ========== DIAGNOSIS-SPECIFIC RECOMMENDATIONS ==========
        
        # Cardiac conditions
        if any(term in diagnosis_lower for term in ["cardiac", "heart", "mi", "infarct", "angina"]):
            recommendations["equipment"].extend([
                "12-lead ECG",
                "Cardiac monitor",
                "Defibrillator",
                "Central line kit"
            ])
            recommendations["medications"].extend([
                "Aspirin 325mg PO (if not given)",
                "Nitroglycerin 0.4mg SL",
                "Morphine 2-4mg IV PRN for pain",
                "Heparin drip",
                "Clopidogrel 300mg loading"
            ])
            recommendations["special_instructions"] += (
                " Cardiac protocol: Serial troponins Q6H. "
                "Keep patient NPO for possible cath lab."
            )
        
        # Respiratory conditions
        elif any(term in diagnosis_lower for term in ["respiratory", "pneumonia", "copd", "asthma", "bronch"]):
            recommendations["equipment"].extend([
                "Nebulizer",
                "Peak flow meter",
                "Chest X-ray order"
            ])
            recommendations["medications"].extend([
                "Albuterol nebulizer Q4H",
                "Ipratropium nebulizer",
                "Azithromycin 500mg IV",
                "Prednisone 40mg PO"
            ])
            recommendations["special_instructions"] += (
                " Respiratory protocol: Elevate head of bed 45 degrees. "
                "Incentive spirometry Q2H when awake."
            )
        
        # Trauma
        elif any(term in diagnosis_lower for term in ["trauma", "accident", "injury", "fracture"]):
            recommendations["equipment"].extend([
                "Blood typing kit",
                "IV fluid warmer",
                "Splints",
                "Cervical collar",
                "Wound care supplies"
            ])
            recommendations["medications"].extend([
                "Tetanus prophylaxis",
                "Morphine 2-4mg IV PRN",
                "Ketorolac 30mg IV",
                "Antibiotics if open wound"
            ])
            recommendations["special_instructions"] += (
                " Trauma protocol: Primary and secondary survey complete. "
                "Keep spine immobilized until cleared."
            )
        
        # Stroke
        elif any(term in diagnosis_lower for term in ["stroke", "cva", "tia", "cerebro"]):
            recommendations["equipment"].extend([
                "NIH Stroke Scale assessment",
                "Blood glucose monitor",
                "CT scan order"
            ])
            recommendations["medications"].extend([
                "tPA if within window (physician only)",
                "Aspirin 325mg (if not hemorrhagic)",
                "Blood pressure management"
            ])
            recommendations["special_instructions"] += (
                " Stroke protocol: Time is brain. Note symptom onset time. "
                "NPO until swallow evaluation. Neurological checks Q1H."
            )
        
        # Sepsis
        elif any(term in diagnosis_lower for term in ["sepsis", "infection", "fever"]):
            recommendations["equipment"].extend([
                "Blood culture kit",
                "Lactate level",
                "IV fluid bolus ready"
            ])
            recommendations["medications"].extend([
                "Broad-spectrum antibiotics within 1 hour",
                "Normal Saline 30mL/kg bolus",
                "Vasopressors if hypotensive"
            ])
            recommendations["urgency"] = "HIGH"
            recommendations["special_instructions"] += (
                " Sepsis bundle: Obtain cultures before antibiotics. "
                "Measure lactate. Fluid resuscitation. Monitor urine output."
            )
        
        # ========== SERIOUS PATIENTS ==========
        elif status == "Serious":
            recommendations["equipment"].extend([
                "Continuous cardiac monitor",
                "IV infusion pump",
                "Supplemental oxygen (standby)"
            ])
            recommendations["urgency"] = "MEDIUM"
            recommendations["monitoring_frequency"] = "Every 2 hours"
        
        # ========== STABLE/RECOVERING ==========
        elif status in ["Stable", "Recovering"]:
            recommendations["urgency"] = "LOW"
            recommendations["monitoring_frequency"] = "Every 4-6 hours"
            recommendations["special_instructions"] = (
                "Continue current treatment plan. "
                "Prepare for possible step-down or discharge planning."
            )
        
        # Remove duplicates from lists
        recommendations["equipment"] = list(dict.fromkeys(recommendations["equipment"]))
        recommendations["medications"] = list(dict.fromkeys(recommendations["medications"]))
        recommendations["warning_signs"] = list(dict.fromkeys(recommendations["warning_signs"]))
        
        return recommendations
    
    def get_quick_recommendation(self, diagnosis: str, status: str, spo2: float, heart_rate: int) -> Dict:
        """
        Get quick recommendation without full Patient object.
        Useful for quick lookups.
        
        Args:
            diagnosis: Patient diagnosis
            status: Patient status string
            spo2: Oxygen saturation
            heart_rate: Heart rate in bpm
            
        Returns:
            Dict with basic recommendations
        """
        # Create temporary patient object
        temp_patient = Patient(
            id="temp",
            name="Temp",
            age=50,
            diagnosis=diagnosis,
            status=PatientStatus(status) if status in [s.value for s in PatientStatus] else PatientStatus.STABLE,
            spo2=spo2,
            heart_rate=heart_rate
        )
        
        return self.get_preparation_checklist(temp_patient)
    
    def clear_cache(self):
        """Clear recommendation cache."""
        self._cache.clear()


# Singleton instance
medicine_ai = MedicineAI()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing MedicineAI...")
    
    # Test 1: Critical cardiac patient (fallback)
    print("\n--- Test 1: Critical Cardiac Patient ---")
    patient1 = Patient(
        id="P001",
        name="John Critical",
        age=65,
        diagnosis="Cardiac Arrest",
        status=PatientStatus.CRITICAL,
        spo2=82.0,
        heart_rate=145
    )
    
    result = medicine_ai.get_preparation_checklist(patient1)
    print(f"Urgency: {result['urgency']}")
    print(f"Equipment ({len(result['equipment'])} items):")
    for eq in result['equipment'][:5]:
        print(f"  - {eq}")
    print(f"Medications ({len(result['medications'])} items):")
    for med in result['medications'][:5]:
        print(f"  - {med}")
    print(f"Special Instructions: {result['special_instructions'][:100]}...")
    
    assert result['urgency'] == 'HIGH', "Critical patient should have HIGH urgency"
    assert 'Defibrillator' in result['equipment'], "Should include defibrillator"
    assert any('Epinephrine' in m for m in result['medications']), "Should include Epinephrine"
    print("✓ Critical patient recommendations correct")
    
    # Test 2: Respiratory patient
    print("\n--- Test 2: Respiratory Patient ---")
    patient2 = Patient(
        id="P002",
        name="Jane Pneumonia",
        age=55,
        diagnosis="Pneumonia with respiratory distress",
        status=PatientStatus.SERIOUS,
        spo2=88.0,
        heart_rate=95
    )
    
    result = medicine_ai.get_preparation_checklist(patient2)
    print(f"Urgency: {result['urgency']}")
    print(f"Equipment: {result['equipment'][:3]}")
    print(f"Medications: {result['medications'][:3]}")
    
    assert 'Nebulizer' in result['equipment'] or 'Oxygen' in str(result['equipment'])
    print("✓ Respiratory patient recommendations correct")
    
    # Test 3: Stable patient
    print("\n--- Test 3: Stable Patient ---")
    patient3 = Patient(
        id="P003",
        name="Bob Stable",
        age=40,
        diagnosis="Minor infection",
        status=PatientStatus.STABLE,
        spo2=97.0,
        heart_rate=75
    )
    
    result = medicine_ai.get_preparation_checklist(patient3)
    print(f"Urgency: {result['urgency']}")
    print(f"Monitoring: {result['monitoring_frequency']}")
    
    assert result['urgency'] == 'LOW', "Stable patient should have LOW urgency"
    print("✓ Stable patient recommendations correct")
    
    # Test 4: Quick recommendation
    print("\n--- Test 4: Quick Recommendation ---")
    quick_result = medicine_ai.get_quick_recommendation(
        diagnosis="Stroke",
        status="Critical",
        spo2=90.0,
        heart_rate=85
    )
    print(f"Urgency: {quick_result['urgency']}")
    assert 'NIH Stroke Scale' in str(quick_result['equipment']) or quick_result['urgency'] == 'HIGH'
    print("✓ Quick recommendation works")
    
    # Test 5: Cache
    print("\n--- Test 5: Cache ---")
    result1 = medicine_ai.get_preparation_checklist(patient1)
    result2 = medicine_ai.get_preparation_checklist(patient1)
    # Should be same object from cache
    assert result1 == result2, "Cached results should match"
    print("✓ Caching works correctly")
    
    medicine_ai.clear_cache()
    print("✓ Cache cleared")
    
    print("\n✅ All MedicineAI tests passed!")
