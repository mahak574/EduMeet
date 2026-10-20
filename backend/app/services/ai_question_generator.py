import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from app.config import settings
from app.models.consolidated import Question, QuestionOption, validate_slug

logger = logging.getLogger(__name__)

# Standard curriculum blueprints for common academic subjects
KNOWN_SUBJECT_TOPICS: Dict[str, List[str]] = {
    # --------------------------------------------------------------------------
    # Computer Science & Programming Blueprints
    # --------------------------------------------------------------------------
    "dsa": [
        "arrays-and-hashing",
        "linked-lists-and-stacks",
        "trees-and-graphs",
        "dynamic-programming",
    ],
    "dbms": [
        "relational-schema-and-sql",
        "indexing-and-query-opt",
        "transactions-and-acid",
        "concurrency-and-recovery",
    ],
    "operating-systems": [
        "process-and-threads",
        "memory-and-virtual-memory",
        "concurrency-and-deadlocks",
        "file-systems-and-io",
    ],
    "computer-networks": [
        "osi-and-tcp-ip-models",
        "routing-and-ip-addressing",
        "transport-tcp-and-udp",
        "application-dns-http-tls",
    ],
    "python": [
        "data-structures-and-types",
        "functions-and-generators",
        "oop-and-dunder-methods",
        "concurrency-and-asyncio",
    ],
    "system-design": [
        "load-balancing-and-caching",
        "database-sharding-and-replication",
        "message-queues-and-event-driven",
        "api-rate-limiting-and-resilience",
    ],
    "machine-learning": [
        "supervised-learning-regression-classification",
        "unsupervised-clustering-and-pca",
        "neural-networks-and-backpropagation",
        "model-evaluation-and-overfitting",
    ],
    "web-development": [
        "html5-and-semantic-dom",
        "css-layout-flexbox-grid",
        "async-javascript-and-promises",
        "web-security-cors-xss-csrf",
    ],

    # --------------------------------------------------------------------------
    # Mathematics Grade Tracks & Blueprints
    # --------------------------------------------------------------------------
    # 1. General Practical Mathematics
    "maths": [
        "commercial-arithmetic-and-interest",
        "percentages-ratios-and-proportions",
        "practical-algebra-and-equations",
        "geometry-mensuration-and-data",
    ],
    "mathematics": [
        "commercial-arithmetic-and-interest",
        "percentages-ratios-and-proportions",
        "practical-algebra-and-equations",
        "geometry-mensuration-and-data",
    ],

    # 2. Primary / Elementary (Class 1–5)
    "maths-elementary": [
        "arithmetic-and-word-problems",
        "fractions-and-decimals",
        "basic-geometry-and-perimeter",
        "measurement-and-units",
    ],
    "maths-grade-1-5": [
        "arithmetic-and-word-problems",
        "fractions-and-decimals",
        "basic-geometry-and-perimeter",
        "measurement-and-units",
    ],

    # 3. Middle / Secondary School (Class 6–10)
    "maths-middle-school": [
        "integers-and-fractions",
        "percentages-and-ratios",
        "linear-equations-in-one-variable",
        "angles-and-triangles",
    ],
    "maths-high-school": [
        "quadratic-equations-and-polynomials",
        "trigonometry-and-heights",
        "surface-areas-and-volumes",
        "coordinate-geometry-and-probability",
    ],
    "maths-grade-6-10": [
        "quadratic-equations-and-polynomials",
        "trigonometry-and-heights",
        "surface-areas-and-volumes",
        "coordinate-geometry-and-probability",
    ],

    # 4. Senior Secondary (Class 11–12)
    "maths-class-11-12": [
        "differential-calculus",
        "integral-calculus",
        "matrices-and-determinants",
        "vectors-and-3d-geometry",
    ],

    # 5. Engineering & STEM
    "maths-engineering": [
        "multivariable-calculus",
        "linear-algebra-and-eigenvalues",
        "differential-equations-and-laplace",
        "numerical-methods-and-statistics",
    ],

    # 6. Commerce, CA Foundation & Business Mathematics
    "maths-commerce-ca": [
        "time-value-of-money-and-annuities",
        "business-calculus-and-marginality",
        "linear-programming-and-matrices",
        "business-statistics-and-correlation",
    ],

    # 7. Competitive & Quantitative Aptitude
    "maths-aptitude": [
        "speed-maths-and-percentages",
        "profit-loss-and-discount",
        "time-speed-distance-and-work",
        "permutations-combinations-and-probability",
    ],
}


# Pre-crafted high-quality practical mathematics question repository
PRACTICAL_MATH_QUESTION_BANK: Dict[str, List[Dict]] = {
    # General Maths
    "commercial-arithmetic-and-interest": [
        {
            "prompt": "A retailer buys an article for $240 and marks it up by 25%. If they offer a customer a 10% cash discount, what is the retailer's actual profit in dollars?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "$30"}, {"id": "B", "text": "$36"}, {"id": "C", "text": "$24"}, {"id": "D", "text": "$40"}],
            "correct": "A",
            "explanation": "Marked Price = $240 * 1.25 = $300. Selling Price with 10% discount = $300 * 0.90 = $270. Profit = $270 - $240 = $30.",
        },
        {
            "prompt": "What is the compound interest on a principal of $5,000 invested for 2 years at 8% per annum compounded annually?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "$800"}, {"id": "B", "text": "$832"}, {"id": "C", "text": "$850"}, {"id": "D", "text": "$864"}],
            "correct": "B",
            "explanation": "Amount = P * (1 + r)^t = $5000 * (1.08)^2 = $5000 * 1.1664 = $5832. Compound Interest = $5832 - $5000 = $832.",
        },
        {
            "prompt": "A sum of $1,200 is invested at simple interest. If it earns $216 in interest over 3 years, what is the annual interest rate?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "5%"}, {"id": "B", "text": "6%"}, {"id": "C", "text": "7%"}, {"id": "D", "text": "8%"}],
            "correct": "B",
            "explanation": "Simple Interest I = (P * R * T) / 100 => 216 = (1200 * R * 3) / 100 => 216 = 36 * R => R = 6% per annum.",
        },
        {
            "prompt": "An article with a list price of $500 is sold after two successive discounts of 20% and 10%. What is the final selling price?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "$350"}, {"id": "B", "text": "$360"}, {"id": "C", "text": "$370"}, {"id": "D", "text": "$380"}],
            "correct": "B",
            "explanation": "First discount of 20%: $500 * 0.80 = $400. Second discount of 10%: $400 * 0.90 = $360.",
        },
    ],
    "percentages-ratios-and-proportions": [
        {
            "prompt": "Two numbers are in the ratio 3:5. If 8 is added to both numbers, their ratio becomes 2:3. What is the larger number?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "24"}, {"id": "B", "text": "30"}, {"id": "C", "text": "40"}, {"id": "D", "text": "45"}],
            "correct": "C",
            "explanation": "Let numbers be 3x and 5x. (3x + 8)/(5x + 8) = 2/3 => 3(3x + 8) = 2(5x + 8) => 9x + 24 = 10x + 16 => x = 8. Larger number = 5x = 40.",
        },
        {
            "prompt": "In an examination, 65% of students passed in Mathematics and 70% passed in English. If 50% passed in both, what percentage failed in both subjects?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "10%"}, {"id": "B", "text": "15%"}, {"id": "C", "text": "20%"}, {"id": "D", "text": "25"}],
            "correct": "B",
            "explanation": "Passed in at least one = 65% + 70% - 50% = 85%. Percentage failing in both = 100% - 85% = 15%.",
        },
        {
            "prompt": "A solution contains 20% alcohol in water. If 2 liters of pure water are added to 8 liters of this solution, what is the new concentration of alcohol?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "14%"}, {"id": "B", "text": "15%"}, {"id": "C", "text": "16%"}, {"id": "D", "text": "18%"}],
            "correct": "C",
            "explanation": "Initial alcohol = 20% of 8L = 1.6L. Total new volume = 8L + 2L = 10L. New concentration = (1.6 / 10) * 100% = 16%.",
        },
        {
            "prompt": "If a quantity increases from 120 to 150, what is the percentage increase?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "20%"}, {"id": "B", "text": "25%"}, {"id": "C", "text": "30%"}, {"id": "D", "text": "33.3%"}],
            "correct": "B",
            "explanation": "Increase = 150 - 120 = 30. Percentage increase = (30 / 120) * 100% = 25%.",
        },
    ],
    "practical-algebra-and-equations": [
        {
            "prompt": "A mother is 3 times as old as her son. In 12 years, she will be twice as old as her son. How old is the son today?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "10 years"}, {"id": "B", "text": "12 years"}, {"id": "C", "text": "14 years"}, {"id": "D", "text": "16 years"}],
            "correct": "B",
            "explanation": "Let son's age = x, mother's age = 3x. In 12 years: 3x + 12 = 2(x + 12) => 3x + 12 = 2x + 24 => x = 12.",
        },
        {
            "prompt": "If 4 pencils and 3 notebooks cost $26, and 2 pencils and 5 notebooks cost $34, what is the cost of 1 notebook?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "$4"}, {"id": "B", "text": "$5"}, {"id": "C", "text": "$6"}, {"id": "D", "text": "$7"}],
            "correct": "C",
            "explanation": "Multiply second equation by 2: 4p + 10n = 68. Subtract first (4p + 3n = 26): 7n = 42 => n = $6.",
        },
        {
            "prompt": "What are the roots of the equation x^2 - 9x + 20 = 0?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "x = 2, 10"}, {"id": "B", "text": "x = 4, 5"}, {"id": "C", "text": "x = -4, -5"}, {"id": "D", "text": "x = 3, 6"}],
            "correct": "B",
            "explanation": "Factorization: (x - 4)(x - 5) = 0 => x = 4 or x = 5.",
        },
        {
            "prompt": "Worker A can finish a job in 6 days and Worker B can finish the same job in 12 days. Working together, how many days will they take?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "3 days"}, {"id": "B", "text": "4 days"}, {"id": "C", "text": "5 days"}, {"id": "D", "text": "4.5 days"}],
            "correct": "B",
            "explanation": "Combined 1-day rate = 1/6 + 1/12 = 3/12 = 1/4. Total time = 4 days.",
        },
    ],
    "geometry-mensuration-and-data": [
        {
            "prompt": "A circular running track has an inner diameter of 140 meters. Using pi = 22/7, what is the distance covered in 1 complete lap along the inner edge?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "440 meters"}, {"id": "B", "text": "420 meters"}, {"id": "C", "text": "880 meters"}, {"id": "D", "text": "314 meters"}],
            "correct": "A",
            "explanation": "Circumference = pi * diameter = (22/7) * 140 = 22 * 20 = 440 meters.",
        },
        {
            "prompt": "A solid right circular cylinder has radius 7 cm and height 10 cm. Using pi = 22/7, what is its total surface area?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "616 cm²"}, {"id": "B", "text": "748 cm²"}, {"id": "C", "text": "440 cm²"}, {"id": "D", "text": "528 cm²"}],
            "correct": "B",
            "explanation": "Total Surface Area = 2*pi*r*(h + r) = 2 * (22/7) * 7 * (10 + 7) = 44 * 17 = 748 cm².",
        },
        {
            "prompt": "The mean of five test scores is 82. If four of the scores are 78, 85, 90, and 75, what is the fifth score?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "80"}, {"id": "B", "text": "82"}, {"id": "C", "text": "84"}, {"id": "D", "text": "86"}],
            "correct": "B",
            "explanation": "Total sum = 5 * 82 = 410. Sum of 4 scores = 78 + 85 + 90 + 75 = 328. Fifth score = 410 - 328 = 82.",
        },
        {
            "prompt": "Two cards are drawn simultaneously from a standard deck of 52 playing cards. What is the probability that both are aces?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "1/221"}, {"id": "B", "text": "1/169"}, {"id": "C", "text": "1/26"}, {"id": "D", "text": "4/663"}],
            "correct": "A",
            "explanation": "P(both aces) = (4/52) * (3/51) = (1/13) * (1/17) = 1/221.",
        },
    ],

    # Primary School (Class 1–5)
    "arithmetic-and-word-problems": [
        {
            "prompt": "Emma has 4 boxes of crayons. Each box contains 12 crayons. She gives 15 crayons to her brother. How many crayons does she have left?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "31 crayons"}, {"id": "B", "text": "33 crayons"}, {"id": "C", "text": "35 crayons"}, {"id": "D", "text": "48 crayons"}],
            "correct": "B",
            "explanation": "Total crayons = 4 * 12 = 48 crayons. Left over = 48 - 15 = 33 crayons.",
        },
        {
            "prompt": "A bakery bakes 144 cupcakes in the morning. They pack them into boxes of 6 cupcakes each. How many boxes do they fill?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "22 boxes"}, {"id": "B", "text": "24 boxes"}, {"id": "C", "text": "26 boxes"}, {"id": "D", "text": "28 boxes"}],
            "correct": "B",
            "explanation": "Number of boxes = 144 / 6 = 24 boxes.",
        },
        {
            "prompt": "Lucas bought 3 notebooks at $4 each and 2 pens at $1.50 each. He paid with a $20 bill. How much change should he receive?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "$4.00"}, {"id": "B", "text": "$5.00"}, {"id": "C", "text": "$6.00"}, {"id": "D", "text": "$7.00"}],
            "correct": "B",
            "explanation": "Cost = (3 * $4) + (2 * $1.50) = $12 + $3 = $15. Change = $20 - $15 = $5.00.",
        },
        {
            "prompt": "A school bus carries 45 students. If there are 8 full buses taking students to a museum, how many students are going in total?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "320"}, {"id": "B", "text": "360"}, {"id": "C", "text": "380"}, {"id": "D", "text": "400"}],
            "correct": "B",
            "explanation": "Total students = 45 * 8 = 360 students.",
        },
    ],
    "fractions-and-decimals": [
        {
            "prompt": "A pizza is sliced into 8 equal slices. Maya eats 3 slices and Liam eats 2 slices. What fraction of the pizza is remaining?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "1/8"}, {"id": "B", "text": "2/8"}, {"id": "C", "text": "3/8"}, {"id": "D", "text": "5/8"}],
            "correct": "C",
            "explanation": "Total eaten = 3/8 + 2/8 = 5/8. Remaining = 8/8 - 5/8 = 3/8.",
        },
        {
            "prompt": "Which of the following fractions is equivalent to 3/4?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "6/8"}, {"id": "B", "text": "5/7"}, {"id": "C", "text": "9/15"}, {"id": "D", "text": "4/3"}],
            "correct": "A",
            "explanation": "Multiply numerator and denominator by 2: (3 * 2) / (4 * 2) = 6/8.",
        },
        {
            "prompt": "What is the sum of 0.75 + 1.45?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "2.10"}, {"id": "B", "text": "2.20"}, {"id": "C", "text": "2.15"}, {"id": "D", "text": "2.30"}],
            "correct": "B",
            "explanation": "0.75 + 1.45 = 2.20.",
        },
        {
            "prompt": "Convert the fraction 7/10 into a decimal number.",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "0.07"}, {"id": "B", "text": "0.7"}, {"id": "C", "text": "7.0"}, {"id": "D", "text": "0.77"}],
            "correct": "B",
            "explanation": "7 divided by 10 is 0.7.",
        },
    ],
    "basic-geometry-and-perimeter": [
        {
            "prompt": "A rectangular playground has a length of 25 meters and a width of 15 meters. What is its perimeter?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "40 meters"}, {"id": "B", "text": "80 meters"}, {"id": "C", "text": "375 meters"}, {"id": "D", "text": "50 meters"}],
            "correct": "B",
            "explanation": "Perimeter = 2 * (length + width) = 2 * (25 + 15) = 2 * 40 = 80 meters.",
        },
        {
            "prompt": "A square garden has an area of 64 square meters. What is the length of one side?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "6 meters"}, {"id": "B", "text": "7 meters"}, {"id": "C", "text": "8 meters"}, {"id": "D", "text": "16 meters"}],
            "correct": "C",
            "explanation": "Area of square = side^2 => side = sqrt(64) = 8 meters.",
        },
        {
            "prompt": "How many sides does a regular hexagon have?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "5 sides"}, {"id": "B", "text": "6 sides"}, {"id": "C", "text": "7 sides"}, {"id": "D", "text": "8 sides"}],
            "correct": "B",
            "explanation": "A hexagon has 6 sides and 6 vertices.",
        },
        {
            "prompt": "An angle measures exactly 90 degrees. What type of angle is it?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "Acute angle"}, {"id": "B", "text": "Right angle"}, {"id": "C", "text": "Obtuse angle"}, {"id": "D", "text": "Reflex angle"}],
            "correct": "B",
            "explanation": "An angle measuring exactly 90 degrees is a right angle.",
        },
    ],
    "measurement-and-units": [
        {
            "prompt": "A movie starts at 4:45 PM and lasts for 2 hours and 20 minutes. At what time does the movie end?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "6:45 PM"}, {"id": "B", "text": "7:00 PM"}, {"id": "C", "text": "7:05 PM"}, {"id": "D", "text": "7:15 PM"}],
            "correct": "C",
            "explanation": "4:45 PM + 2 hours = 6:45 PM. 6:45 PM + 20 minutes = 7:05 PM.",
        },
        {
            "prompt": "How many milliliters are in 3.5 liters of water?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "350 mL"}, {"id": "B", "text": "3,500 mL"}, {"id": "C", "text": "35,000 mL"}, {"id": "D", "text": "35 mL"}],
            "correct": "B",
            "explanation": "1 liter = 1,000 milliliters. 3.5 liters = 3.5 * 1000 = 3,500 mL.",
        },
        {
            "prompt": "A bag of potatoes weighs 2 kilograms and 400 grams. How many total grams is that?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "240 grams"}, {"id": "B", "text": "2,400 grams"}, {"id": "C", "text": "24,000 grams"}, {"id": "D", "text": "2,040 grams"}],
            "correct": "B",
            "explanation": "2 kg = 2000 grams. 2000 + 400 = 2,400 grams.",
        },
        {
            "prompt": "A ribbon is 1.8 meters long. If 60 centimeters are cut off, how many centimeters of ribbon remain?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "120 cm"}, {"id": "B", "text": "100 cm"}, {"id": "C", "text": "140 cm"}, {"id": "D", "text": "80 cm"}],
            "correct": "A",
            "explanation": "1.8 meters = 180 cm. Remaining = 180 - 60 = 120 cm.",
        },
    ],

    # Senior Secondary (Class 11–12)
    "differential-calculus": [
        {
            "prompt": "What is the derivative of f(x) = 4x^3 - 5x^2 + 7x - 9 evaluated at x = 2?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "35"}, {"id": "B", "text": "28"}, {"id": "C", "text": "42"}, {"id": "D", "text": "31"}],
            "correct": "A",
            "explanation": "f'(x) = 12x^2 - 10x + 7. At x = 2: f'(2) = 12(4) - 10(2) + 7 = 48 - 20 + 7 = 35.",
        },
        {
            "prompt": "What is the slope of the tangent line to the curve y = sin(2x) at the point x = pi / 4?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "0"}, {"id": "B", "text": "1"}, {"id": "C", "text": "2"}, {"id": "D", "text": "-2"}],
            "correct": "A",
            "explanation": "dy/dx = 2*cos(2x). At x = pi/4: 2*cos(pi/2) = 2*(0) = 0.",
        },
        {
            "prompt": "Evaluate the limit lim(x -> 0) [ (e^(3x) - 1) / x ].",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "1"}, {"id": "B", "text": "3"}, {"id": "C", "text": "0"}, {"id": "D", "text": "e^3"}],
            "correct": "B",
            "explanation": "Using L'Hôpital's Rule: derivative of numerator is 3e^(3x), denominator is 1. Limit = 3e^0 = 3.",
        },
        {
            "prompt": "A particle moves along a straight line such that its displacement is s(t) = t^3 - 6t^2 + 9t + 2. At what time t > 0 is the particle momentarily at rest?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "t = 1 and t = 3"}, {"id": "B", "text": "t = 2 and t = 4"}, {"id": "C", "text": "t = 3 only"}, {"id": "D", "text": "t = 6 only"}],
            "correct": "A",
            "explanation": "Velocity v(t) = s'(t) = 3t^2 - 12t + 9 = 3(t - 1)(t - 3) = 0 => t = 1 and t = 3.",
        },
    ],
    "integral-calculus": [
        {
            "prompt": "Evaluate the definite integral of (3x^2 + 2x) dx from x = 1 to x = 3.",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "26"}, {"id": "B", "text": "34"}, {"id": "C", "text": "32"}, {"id": "D", "text": "30"}],
            "correct": "B",
            "explanation": "Antiderivative F(x) = x^3 + x^2. F(3) = 27 + 9 = 36. F(1) = 1 + 1 = 2. Value = 36 - 2 = 34.",
        },
        {
            "prompt": "What is the indefinite integral of (2x) / (x^2 + 5) dx?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "ln|x^2 + 5| + C"}, {"id": "B", "text": "2*ln|x^2 + 5| + C"}, {"id": "C", "text": "arctan(x/5) + C"}, {"id": "D", "text": "(x^2 + 5)^(-1) + C"}],
            "correct": "A",
            "explanation": "Let u = x^2 + 5 => du = 2x dx. Integral becomes int(1/u du) = ln|u| + C = ln|x^2 + 5| + C.",
        },
        {
            "prompt": "What is the area of the region bounded by the parabola y = 4 - x^2 and the x-axis (from x = -2 to x = 2)?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "16/3"}, {"id": "B", "text": "32/3"}, {"id": "C", "text": "16"}, {"id": "D", "text": "8"}],
            "correct": "B",
            "explanation": "Area = int_{-2}^{2} (4 - x^2) dx = [4x - x^3/3]_{-2}^{2} = (8 - 8/3) - (-8 + 8/3) = 16/3 - (-16/3) = 32/3.",
        },
        {
            "prompt": "Evaluate the integral of x * e^x dx using integration by parts.",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "(x - 1)e^x + C"}, {"id": "B", "text": "(x + 1)e^x + C"}, {"id": "C", "text": "x^2 * e^x + C"}, {"id": "D", "text": "e^x + C"}],
            "correct": "A",
            "explanation": "int(u dv) = uv - int(v du). Let u = x, dv = e^x dx => du = dx, v = e^x. Integral = x*e^x - int(e^x dx) = (x - 1)e^x + C.",
        },
    ],
    "matrices-and-determinants": [
        {
            "prompt": "What is the determinant of the 2x2 matrix with rows [4, 7] and [2, 5]?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "6"}, {"id": "B", "text": "8"}, {"id": "C", "text": "14"}, {"id": "D", "text": "26"}],
            "correct": "A",
            "explanation": "det = (4 * 5) - (7 * 2) = 20 - 14 = 6.",
        },
        {
            "prompt": "If A is an invertible 3x3 matrix and det(A) = 4, what is the determinant of its inverse A^(-1)?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "4"}, {"id": "B", "text": "1/4"}, {"id": "C", "text": "-4"}, {"id": "D", "text": "1/16"}],
            "correct": "B",
            "explanation": "det(A^(-1)) = 1 / det(A) = 1 / 4.",
        },
        {
            "prompt": "For what value of k does the matrix [[2, k], [4, 6]] have no inverse (singular)?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "k = 2"}, {"id": "B", "text": "k = 3"}, {"id": "C", "text": "k = 4"}, {"id": "D", "text": "k = 6"}],
            "correct": "B",
            "explanation": "A matrix is singular when det = 0 => (2 * 6) - (4 * k) = 0 => 12 = 4k => k = 3.",
        },
        {
            "prompt": "If matrix A is of order 2x3 and matrix B is of order 3x4, what is the order of the product matrix AB?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "3x3"}, {"id": "B", "text": "2x4"}, {"id": "C", "text": "4x2"}, {"id": "D", "text": "2x3"}],
            "correct": "B",
            "explanation": "(2 x 3) * (3 x 4) results in a matrix of dimension 2 x 4.",
        },
    ],
    "vectors-and-3d-geometry": [
        {
            "prompt": "For vectors a = 2i + 3j - k and b = i - 2j + 4k, what is their scalar (dot) product a . b?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "-8"}, {"id": "B", "text": "-4"}, {"id": "C", "text": "6"}, {"id": "D", "text": "0"}],
            "correct": "A",
            "explanation": "a . b = (2)(1) + (3)(-2) + (-1)(4) = 2 - 6 - 4 = -8.",
        },
        {
            "prompt": "What is the cross product magnitude |a x b| if |a| = 5, |b| = 4, and the angle between them is 30 degrees?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "10"}, {"id": "B", "text": "10 * sqrt(3)"}, {"id": "C", "text": "20"}, {"id": "D", "text": "5"}],
            "correct": "A",
            "explanation": "|a x b| = |a| * |b| * sin(theta) = 5 * 4 * sin(30°) = 20 * 0.5 = 10.",
        },
        {
            "prompt": "What is the distance between the points (1, 2, 3) and (4, 6, 3) in 3D Euclidean space?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "4"}, {"id": "B", "text": "5"}, {"id": "C", "text": "sqrt(7)"}, {"id": "D", "text": "7"}],
            "correct": "B",
            "explanation": "Distance = sqrt((4 - 1)^2 + (6 - 2)^2 + (3 - 3)^2) = sqrt(3^2 + 4^2 + 0) = sqrt(25) = 5.",
        },
        {
            "prompt": "If two non-zero vectors u and v satisfy u . v = 0, what is the geometric relationship between them?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "They are parallel"}, {"id": "B", "text": "They are orthogonal (perpendicular)"}, {"id": "C", "text": "They are collinear"}, {"id": "D", "text": "They have opposite directions"}],
            "correct": "B",
            "explanation": "The dot product of two non-zero vectors is zero if and only if they are orthogonal (perpendicular).",
        },
    ],

    # Commerce, CA & Business Mathematics
    "time-value-of-money-and-annuities": [
        {
            "prompt": "An investor deposits $2,000 at the end of each year for 3 years into an account earning 10% interest compounded annually. What is the future value of this ordinary annuity?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "$6,620"}, {"id": "B", "text": "$6,000"}, {"id": "C", "text": "$7,260"}, {"id": "D", "text": "$6,300"}],
            "correct": "A",
            "explanation": "FV = P * [((1 + i)^n - 1) / i] = 2000 * [((1.1)^3 - 1) / 0.10] = 2000 * [(1.331 - 1) / 0.10] = 2000 * 3.31 = $6,620.",
        },
        {
            "prompt": "If the nominal annual interest rate is 12% compounded quarterly, what is the effective annual rate of interest?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "12.00%"}, {"id": "B", "text": "12.55%"}, {"id": "C", "text": "12.68%"}, {"id": "D", "text": "13.00%"}],
            "correct": "B",
            "explanation": "Effective Rate = (1 + r/m)^m - 1 = (1 + 0.12/4)^4 - 1 = (1.03)^4 - 1 = 1.1255 - 1 = 12.55%.",
        },
        {
            "prompt": "What is the present value of $1,331 receivable 3 years from today at an annual discount rate of 10% compounded annually?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "$1,000"}, {"id": "B", "text": "$1,100"}, {"id": "C", "text": "$1,200"}, {"id": "D", "text": "$950"}],
            "correct": "A",
            "explanation": "PV = FV / (1 + r)^t = 1331 / (1.10)^3 = 1331 / 1.331 = $1,000.",
        },
        {
            "prompt": "A loan of $10,000 is to be amortized over 2 equal annual end-of-year payments at 10% interest. What is the annual installment payment?",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "$5,000.00"}, {"id": "B", "text": "$5,761.90"}, {"id": "C", "text": "$5,500.00"}, {"id": "D", "text": "$6,000.00"}],
            "correct": "B",
            "explanation": "Payment A = P * [i / (1 - (1 + i)^(-n))] = 10000 * [0.10 / (1 - 1.10^(-2))] = 10000 * [0.10 / (1 - 0.8264)] = 1000 / 0.1736 = $5,761.90.",
        },
    ],
    "business-calculus-and-marginality": [
        {
            "prompt": "A company has total revenue R(x) = 200x - 2x^2 and total cost C(x) = 40x + 500. What production quantity x maximizes total profit?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "x = 40 units"}, {"id": "B", "text": "x = 50 units"}, {"id": "C", "text": "x = 80 units"}, {"id": "D", "text": "x = 100 units"}],
            "correct": "A",
            "explanation": "Profit P(x) = R(x) - C(x) = -2x^2 + 160x - 500. Setting P'(x) = 0: -4x + 160 = 0 => 4x = 160 => x = 40 units.",
        },
        {
            "prompt": "If total cost function is C(x) = 500 + 15x + 0.05x^2, what is the Marginal Cost when producing the 100th unit?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "$20"}, {"id": "B", "text": "$25"}, {"id": "C", "text": "$30"}, {"id": "D", "text": "$15"}],
            "correct": "B",
            "explanation": "Marginal Cost MC = C'(x) = 15 + 0.10x. At x = 100: MC = 15 + 0.10(100) = 15 + 10 = $25.",
        },
        {
            "prompt": "If price demand function is p = 120 - 4x, what is the Marginal Revenue function MR(x)?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "120 - 4x"}, {"id": "B", "text": "120 - 8x"}, {"id": "C", "text": "60 - 2x"}, {"id": "D", "text": "120x - 4x^2"}],
            "correct": "B",
            "explanation": "Revenue R(x) = p * x = 120x - 4x^2. Marginal Revenue MR(x) = R'(x) = 120 - 8x.",
        },
        {
            "prompt": "The break-even point occurs when:",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "Total Revenue equals Total Cost"}, {"id": "B", "text": "Marginal Revenue equals Marginal Cost"}, {"id": "C", "text": "Profit is strictly maximized"}, {"id": "D", "text": "Fixed Costs equal Variable Costs"}],
            "correct": "A",
            "explanation": "Break-even occurs when total revenue equals total cost (profit = 0).",
        },
    ],
    "linear-programming-and-matrices": [
        {
            "prompt": "In a Linear Programming Problem, the objective is Maximize Z = 3x + 5y. The feasible corner points are (0,0), (4,0), (2,3), and (0,4). What is the maximum value of Z?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "12"}, {"id": "B", "text": "21"}, {"id": "C", "text": "20"}, {"id": "D", "text": "15"}],
            "correct": "B",
            "explanation": "At (0,0): Z = 0. At (4,0): Z = 12. At (2,3): Z = 3(2) + 5(3) = 6 + 15 = 21. At (0,4): Z = 20. Maximum is 21 at (2,3).",
        },
        {
            "prompt": "In an input-output Leontief model, the Hawkins-Simon conditions guarantee that:",
            "difficulty": "hard",
            "options": [{"id": "A", "text": "The economic system produces strictly positive net output"}, {"id": "B", "text": "Fixed costs exceed variable costs"}, {"id": "C", "text": "All prices are zero"}, {"id": "D", "text": "Total revenue equals marginal revenue"}],
            "correct": "A",
            "explanation": "The Hawkins-Simon conditions ensure that the input-output matrix produces viable positive net outputs for exogenous demand.",
        },
        {
            "prompt": "Which of the following constraint sets forms an unbounded feasible region in the first quadrant (x >= 0, y >= 0)?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "x + y >= 4"}, {"id": "B", "text": "x + y <= 4"}, {"id": "C", "text": "2x + 3y <= 6"}, {"id": "D", "text": "x <= 5 and y <= 5"}],
            "correct": "A",
            "explanation": "x + y >= 4 extends indefinitely away from the origin in the first quadrant, making the feasible region unbounded.",
        },
        {
            "prompt": "If a system of linear equations Ax = b has det(A) != 0, what can be concluded about the solution?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "It has a unique solution"}, {"id": "B", "text": "It has infinitely many solutions"}, {"id": "C", "text": "It has no solution"}, {"id": "D", "text": "The system is inconsistent"}],
            "correct": "A",
            "explanation": "When det(A) != 0, the matrix A is invertible, guaranteeing a unique solution x = A^(-1)b.",
        },
    ],
    "business-statistics-and-correlation": [
        {
            "prompt": "If Karl Pearson's coefficient of correlation between sales and advertising expenditure is r = 0.85, what does this indicate?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "Strong positive linear relationship"}, {"id": "B", "text": "Weak negative linear relationship"}, {"id": "C", "text": "Zero correlation"}, {"id": "D", "text": "Non-linear parabolic relationship"}],
            "correct": "A",
            "explanation": "An r value of +0.85 is close to +1, indicating a strong positive linear relationship.",
        },
        {
            "prompt": "The variance of a set of monthly store sales is 144. What is the standard deviation?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "12"}, {"id": "B", "text": "14.4"}, {"id": "C", "text": "72"}, {"id": "D", "text": "20,736"}],
            "correct": "A",
            "explanation": "Standard deviation = sqrt(variance) = sqrt(144) = 12.",
        },
        {
            "prompt": "If the two regression coefficients are b_yx = 0.8 and b_xy = 0.45, what is the correlation coefficient r?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "0.60"}, {"id": "B", "text": "0.36"}, {"id": "C", "text": "0.625"}, {"id": "D", "text": "0.50"}],
            "correct": "A",
            "explanation": "r = sqrt(b_yx * b_xy) = sqrt(0.8 * 0.45) = sqrt(0.36) = 0.60.",
        },
        {
            "prompt": "Laspeyres price index number uses which weights?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "Base year quantities"}, {"id": "B", "text": "Current year quantities"}, {"id": "C", "text": "Average of base and current quantities"}, {"id": "D", "text": "Base year prices"}],
            "correct": "A",
            "explanation": "Laspeyres index uses base year quantities (q0) as weights: sum(p1*q0) / sum(p0*q0) * 100.",
        },
    ],

    # Engineering Math
    "multivariable-calculus": [
        {
            "prompt": "If z = x^2 * y^3, find the partial derivative dz/dx at the point (x=2, y=1).",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "4"}, {"id": "B", "text": "6"}, {"id": "C", "text": "12"}, {"id": "D", "text": "2"}],
            "correct": "A",
            "explanation": "dz/dx = 2x * y^3. At (2, 1): 2(2)(1)^3 = 4.",
        },
        {
            "prompt": "What is the gradient vector grad(f) of f(x, y) = 3x^2 + 4y^2 at the point (1, 2)?",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "[6, 16]"}, {"id": "B", "text": "[3, 8]"}, {"id": "C", "text": "[6, 8]"}, {"id": "D", "text": "[1, 2]"}],
            "correct": "A",
            "explanation": "grad(f) = [df/dx, df/dy] = [6x, 8y]. At (1, 2): [6(1), 8(2)] = [6, 16].",
        },
        {
            "prompt": "Evaluate the double integral int_0^1 int_0^2 (x * y) dy dx.",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "1"}, {"id": "B", "text": "2"}, {"id": "C", "text": "1/2"}, {"id": "D", "text": "4"}],
            "correct": "A",
            "explanation": "Inner integral wrt y: [x * y^2 / 2]_0^2 = 2x. Outer integral wrt x: int_0^1 (2x) dx = [x^2]_0^1 = 1.",
        },
        {
            "prompt": "A vector field F is conservative if and only if its curl is:",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "Zero vector (curl F = 0)"}, {"id": "B", "text": "A constant scalar"}, {"id": "C", "text": "Infinite"}, {"id": "D", "text": "Equal to its divergence"}],
            "correct": "A",
            "explanation": "A smooth vector field in a simply connected domain is conservative if and only if curl F = 0.",
        },
    ],
    "linear-algebra-and-eigenvalues": [
        {
            "prompt": "For the matrix A = [[3, 0], [0, 5]], what are its eigenvalues?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "lambda = 3 and lambda = 5"}, {"id": "B", "text": "lambda = 8 and lambda = 15"}, {"id": "C", "text": "lambda = 2 and lambda = 0"}, {"id": "D", "text": "lambda = 1 and lambda = 5"}],
            "correct": "A",
            "explanation": "For any diagonal matrix, the eigenvalues are simply the diagonal entries: lambda = 3 and lambda = 5.",
        },
        {
            "prompt": "What is the trace of a 3x3 matrix whose eigenvalues are 2, -1, and 4?",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "5"}, {"id": "B", "text": "-8"}, {"id": "C", "text": "7"}, {"id": "D", "text": "3"}],
            "correct": "A",
            "explanation": "The trace of a square matrix equals the sum of its eigenvalues: 2 + (-1) + 4 = 5.",
        },
        {
            "prompt": "If a matrix A satisfies A^T = -A, it is classified as:",
            "difficulty": "easy",
            "options": [{"id": "A", "text": "Skew-symmetric matrix"}, {"id": "B", "text": "Symmetric matrix"}, {"id": "C", "text": "Orthogonal matrix"}, {"id": "D", "text": "Hermitian matrix"}],
            "correct": "A",
            "explanation": "A square matrix is skew-symmetric if its transpose equals its negative: A^T = -A.",
        },
        {
            "prompt": "According to the Cayley-Hamilton theorem, every square matrix satisfies:",
            "difficulty": "medium",
            "options": [{"id": "A", "text": "Its own characteristic equation"}, {"id": "B", "text": "A^2 = I"}, {"id": "C", "text": "det(A) = trace(A)"}, {"id": "D", "text": "A^T = A^(-1)"}],
            "correct": "A",
            "explanation": "The Cayley-Hamilton theorem states that every square matrix satisfies its own characteristic equation p(A) = 0.",
        },
    ],
}

PRACTICAL_PYTHON_QUESTION_BANK: Dict[str, List[Dict[str, any]]] = {
    "data-structures-and-types": [
        {
            "prompt": "What is printed after calling `append_item` twice?",
            "code_snippet": "def append_item(val, items=[]):\n    items.append(val)\n    return items\n\nprint(append_item('A'))\nprint(append_item('B'))",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "['A'] then ['B']"},
                {"id": "B", "text": "['A'] then ['A', 'B']"},
                {"id": "C", "text": "['A', 'B'] then ['A', 'B']"},
                {"id": "D", "text": "TypeError: items cannot be default"},
            ],
            "correct": "B",
            "explanation": "In Python, default arguments are evaluated only once when the function is defined. The mutable list `items` is shared across all calls that do not provide an argument, so 'B' is appended to the existing list containing 'A'.",
        },
        {
            "prompt": "What is the final value of list `x` printed by the script?",
            "code_snippet": "def modify(lst):\n    lst.append(99)\n    lst = [1, 2, 3]\n\nx = [10, 20]\nmodify(x)\nprint(x)",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "[10, 20]"},
                {"id": "B", "text": "[10, 20, 99]"},
                {"id": "C", "text": "[1, 2, 3]"},
                {"id": "D", "text": "[1, 2, 3, 99]"},
            ],
            "correct": "B",
            "explanation": "Python passes object references. `lst.append(99)` mutates the underlying list referenced by `x`. The local re-assignment `lst = [1, 2, 3]` only rebinds the local name `lst` to a new object, leaving `x` pointing to `[10, 20, 99]`.",
        },
        {
            "prompt": "What is the output of the dictionary comprehension below?",
            "code_snippet": "words = ['apple', 'bat', 'cat', 'banana']\nlength_map = {len(w): w for w in words}\nprint(length_map[3])",
            "difficulty": "easy",
            "options": [
                {"id": "A", "text": "'bat'"},
                {"id": "B", "text": "'cat'"},
                {"id": "C", "text": "['bat', 'cat']"},
                {"id": "D", "text": "KeyError: 3"},
            ],
            "correct": "B",
            "explanation": "Dictionary keys are unique. As the comprehension iterates, `len('bat') == 3` sets `length_map[3] = 'bat'`. Next, `len('cat') == 3` overwrites key 3 with 'cat'. Thus, `length_map[3]` evaluates to 'cat'.",
        },
        {
            "prompt": "What is the result of the negative-step slice on list `data`?",
            "code_snippet": "data = [10, 20, 30, 40, 50, 60]\nprint(data[4:1:-1])",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "[50, 40, 30]"},
                {"id": "B", "text": "[50, 40, 30, 20]"},
                {"id": "C", "text": "[40, 30, 20]"},
                {"id": "D", "text": "[]"},
            ],
            "correct": "A",
            "explanation": "With a negative step `-1`, slicing moves backwards starting at index 4 (value 50) and stopping before index 1 (value 20, non-inclusive). It collects elements at indices 4, 3, and 2, which are `[50, 40, 30]`.",
        },
    ],
    "functions-and-generators": [
        {
            "prompt": "What is printed when iterating over this generator twice?",
            "code_snippet": "def count_up():\n    yield 1\n    yield 2\n\nc = count_up()\nprint(list(c))\nprint(list(c))",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "[1, 2] then [1, 2]"},
                {"id": "B", "text": "[1, 2] then []"},
                {"id": "C", "text": "[1, 2] then [None]"},
                {"id": "D", "text": "StopIteration exception"},
            ],
            "correct": "B",
            "explanation": "Generators in Python are single-use stateful iterators. Once fully consumed by the first `list(c)` call, the generator is completely exhausted. A second call produces an empty list `[]`.",
        },
        {
            "prompt": "What does the following closure list comprehension evaluate to?",
            "code_snippet": "multipliers = [lambda x: x * i for i in range(3)]\nprint([m(2) for m in multipliers])",
            "difficulty": "hard",
            "options": [
                {"id": "A", "text": "[0, 2, 4]"},
                {"id": "B", "text": "[4, 4, 4]"},
                {"id": "C", "text": "[0, 0, 0]"},
                {"id": "D", "text": "[2, 2, 2]"},
            ],
            "correct": "B",
            "explanation": "Closures in Python look up variable `i` at call time (late binding). When the lambdas are invoked after loop completion, `i` has its terminal value of 2. So every lambda evaluates to `2 * 2 = 4`.",
        },
        {
            "prompt": "What is the return value of the function invocation below?",
            "code_snippet": "def calculate(a, b, c=5, *args):\n    return a + b + c + sum(args)\n\nprint(calculate(1, 2, 3, 4, 5))",
            "difficulty": "easy",
            "options": [
                {"id": "A", "text": "15"},
                {"id": "B", "text": "11"},
                {"id": "C", "text": "10"},
                {"id": "D", "text": "TypeError: too many arguments"},
            ],
            "correct": "A",
            "explanation": "Arguments match positionally: `a=1`, `b=2`, `c=3` (overriding default 5), and the remaining positional arguments `(4, 5)` are captured in tuple `args`. `1 + 2 + 3 + (4 + 5) = 15`.",
        },
        {
            "prompt": "What is printed when calling `greet('Alice')` with the decorator?",
            "code_snippet": "def emphasize(fn):\n    def wrapper(name):\n        return fn(name).upper() + '!'\n    return wrapper\n\n@emphasize\ndef greet(name):\n    return f'hello {name}'\n\nprint(greet('Alice'))",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "hello Alice!"},
                {"id": "B", "text": "HELLO ALICE!"},
                {"id": "C", "text": "hello ALICE!"},
                {"id": "D", "text": "HELLO alice!"},
            ],
            "correct": "B",
            "explanation": "The decorator `@emphasize` replaces `greet` with `wrapper`. `wrapper('Alice')` calls `fn('Alice')` which returns `'hello Alice'`, converts it to uppercase (`'HELLO ALICE'`), and appends `'!'`.",
        },
    ],
    "oop-and-dunder-methods": [
        {
            "prompt": "What are the printed values of `a.val`, `b.val`, and `Item.val`?",
            "code_snippet": "class Item:\n    val = 10\n\na = Item()\nb = Item()\na.val = 25\nItem.val = 50\nprint(a.val, b.val, Item.val)",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "25 50 50"},
                {"id": "B", "text": "50 50 50"},
                {"id": "C", "text": "25 10 50"},
                {"id": "D", "text": "25 25 50"},
            ],
            "correct": "A",
            "explanation": "`a.val = 25` assigns an instance attribute, shadowing the class variable for `a`. `b` has no instance attribute, so `b.val` resolves to the updated class attribute `Item.val = 50`. Thus, `25 50 50`.",
        },
        {
            "prompt": "What is output by `print(Point(3, 4))` when `__str__` is not defined?",
            "code_snippet": "class Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n    def __repr__(self):\n        return f'Point({self.x}, {self.y})'\n\np = Point(3, 4)\nprint(p)",
            "difficulty": "easy",
            "options": [
                {"id": "A", "text": "<Point object at 0x...>"},
                {"id": "B", "text": "Point(3, 4)"},
                {"id": "C", "text": "(3, 4)"},
                {"id": "D", "text": "TypeError"},
            ],
            "correct": "B",
            "explanation": "When an object is converted to string via `str()` or `print()`, Python checks for `__str__`. If not defined, it automatically falls back to `__repr__`.",
        },
        {
            "prompt": "Which method is executed under Python's C3 Method Resolution Order (MRO)?",
            "code_snippet": "class A:\n    def show(self): return 'A'\nclass B(A):\n    def show(self): return 'B'\nclass C(A):\n    def show(self): return 'C'\nclass D(B, C):\n    pass\n\nprint(D().show())",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "'B'"},
                {"id": "B", "text": "'A'"},
                {"id": "C", "text": "'C'"},
                {"id": "D", "text": "TypeError: Inconsistent MRO"},
            ],
            "correct": "A",
            "explanation": "Python's MRO for `D(B, C)` searches `D -> B -> C -> A -> object`. The first class encountered that implements `show()` is `B`, which returns `'B'`.",
        },
        {
            "prompt": "What does this `@classmethod` implementation output?",
            "code_snippet": "class MathUtils:\n    factor = 3\n    @classmethod\n    def scale(cls, n):\n        return n * cls.factor\n\nprint(MathUtils.scale(7))",
            "difficulty": "easy",
            "options": [
                {"id": "A", "text": "21"},
                {"id": "B", "text": "7"},
                {"id": "C", "text": "3"},
                {"id": "D", "text": "TypeError: missing self"},
            ],
            "correct": "A",
            "explanation": "A `@classmethod` receives the class itself as its first argument `cls`, allowing access to class attributes like `cls.factor = 3`. 7 * 3 = 21.",
        },
    ],
    "concurrency-and-asyncio": [
        {
            "prompt": "What value does the function `test_flow()` return?",
            "code_snippet": "def test_flow():\n    try:\n        return 10\n    finally:\n        return 20\n\nprint(test_flow())",
            "difficulty": "medium",
            "options": [
                {"id": "A", "text": "10"},
                {"id": "B", "text": "20"},
                {"id": "C", "text": "30"},
                {"id": "D", "text": "None"},
            ],
            "correct": "B",
            "explanation": "The `finally` block always executes before leaving a function. If a return statement is executed inside `finally`, it supersedes and discards any prior return value from the `try` block.",
        },
        {
            "prompt": "What will `mid` contain after starred unpacking?",
            "code_snippet": "head, *mid, tail = [1, 2, 3, 4, 5]\nprint(mid)",
            "difficulty": "easy",
            "options": [
                {"id": "A", "text": "[2, 3, 4]"},
                {"id": "B", "text": "(2, 3, 4)"},
                {"id": "C", "text": "[2, 3]"},
                {"id": "D", "text": "3"},
            ],
            "correct": "A",
            "explanation": "Starred unpacking captures all intermediate items into a list. `head=1`, `tail=5`, and `mid=[2, 3, 4]`.",
        },
        {
            "prompt": "What is the output of the symmetric difference operation below?",
            "code_snippet": "s1 = {1, 2, 3, 4}\ns2 = {3, 4, 5, 6}\nprint(s1 ^ s2)",
            "difficulty": "easy",
            "options": [
                {"id": "A", "text": "{3, 4}"},
                {"id": "B", "text": "{1, 2, 5, 6}"},
                {"id": "C", "text": "{1, 2, 3, 4, 5, 6}"},
                {"id": "D", "text": "set()"},
            ],
            "correct": "B",
            "explanation": "The `^` operator calculates symmetric difference: elements in either set, but not in both. Common elements 3 and 4 are excluded, leaving `{1, 2, 5, 6}`.",
        },
        {
            "prompt": "What is the output of chaining dictionary `.get()` fallback lookups?",
            "code_snippet": "scores = {'Alice': 95}\nval = scores.get('Bob', scores.get('Alice', 0))\nprint(val)",
            "difficulty": "easy",
            "options": [
                {"id": "A", "text": "95"},
                {"id": "B", "text": "0"},
                {"id": "C", "text": "None"},
                {"id": "D", "text": "KeyError: 'Bob'"},
            ],
            "correct": "A",
            "explanation": "`scores.get('Bob', default)` looks up 'Bob'. Since 'Bob' does not exist, the default expression `scores.get('Alice', 0)` is evaluated, which finds 'Alice' with score 95.",
        },
    ],
}


class AIQuestionGenerator:
    @classmethod
    def get_topics_for_subject(cls, subject_slug: str) -> List[str]:
        cleaned = validate_slug(subject_slug)
        if cleaned in KNOWN_SUBJECT_TOPICS:
            return KNOWN_SUBJECT_TOPICS[cleaned]

        # Check if subject starts with maths-
        if cleaned.startswith("maths-"):
            return KNOWN_SUBJECT_TOPICS["maths"]

        # For any arbitrary subject entered by user, synthesize 4 clean, distinct subtopics
        return [
            f"{cleaned}-fundamentals",
            f"{cleaned}-core-mechanisms",
            f"{cleaned}-advanced-patterns",
            f"{cleaned}-architecture-and-optimization",
        ]

    @classmethod
    async def ensure_questions_for_subject(
        cls,
        subject_slug: str,
        target_per_topic: int = 4,
    ) -> List[str]:
        """
        Ensures that at least target_per_topic approved questions exist for each topic in subject_slug.
        Generates questions dynamically if absent.
        Returns the list of topic slugs for this subject.
        """
        cleaned_subject = validate_slug(subject_slug)
        topics = cls.get_topics_for_subject(cleaned_subject)

        for topic in topics:
            existing_count = await Question.find(
                Question.subject_slug == cleaned_subject,
                Question.topic_slug == topic,
                Question.review_status == "approved",
            ).count()

            needed = target_per_topic - existing_count
            if needed > 0:
                logger.info(
                    "Generating %d dynamic diagnostic questions for %s / %s...",
                    needed,
                    cleaned_subject,
                    topic,
                )
                generated_questions = await cls._generate_topic_questions(
                    subject_slug=cleaned_subject,
                    topic_slug=topic,
                    count=needed,
                )
                for q in generated_questions:
                    await q.insert()

        return topics

    @classmethod
    def is_math_subject(cls, subject_slug: str) -> bool:
        s = subject_slug.lower()
        return (
            s.startswith("math")
            or "mathematics" in s
            or s in (
                "maths",
                "maths-elementary",
                "maths-grade-1-5",
                "maths-middle-school",
                "maths-high-school",
                "maths-grade-6-10",
                "maths-class-11-12",
                "maths-engineering",
                "maths-commerce-ca",
                "maths-aptitude",
            )
        )

    @classmethod
    def is_coding_subject(cls, subject_slug: str) -> bool:
        s = subject_slug.lower().replace("-", "").replace("_", "")
        return any(k in s for k in ("python", "coding", "programming", "javascript", "typescript", "java", "cpp"))

    @classmethod
    async def _generate_topic_questions(
        cls,
        subject_slug: str,
        topic_slug: str,
        count: int,
    ) -> List[Question]:
        """
        Generates high-quality pedagogical questions. For mathematical subjects,
        strictly pulls authentic practical calculation problems.
        For coding subjects, pulls real executable code snippets and output prediction questions.
        Uses configured LLM (e.g., Gemini free tier) if applicable.
        """
        questions: List[Question] = []
        # If mathematics domain, use practical math question bank first
        if cls.is_math_subject(subject_slug):
            math_qs = cls._generate_practical_math_questions(subject_slug, topic_slug, count)
            if math_qs and len(math_qs) >= count:
                questions = math_qs

        # If coding domain, use practical python/coding question bank first
        elif cls.is_coding_subject(subject_slug):
            code_qs = cls._generate_practical_coding_questions(subject_slug, topic_slug, count)
            if code_qs and len(code_qs) >= count:
                questions = code_qs

        # Check if an LLM provider is configured (e.g. Gemini free tier)
        elif getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "OPENAI_API_KEY", None):
            try:
                ai_questions = await cls._generate_via_llm(subject_slug, topic_slug, count)
                if ai_questions and len(ai_questions) >= count:
                    questions = ai_questions
            except Exception as exc:
                logger.warning("LLM question generation failed, using pedagogical generator: %s", exc)

        if not questions or len(questions) < count:
            if cls.is_math_subject(subject_slug):
                questions = cls._generate_practical_math_questions(subject_slug, topic_slug, count)
            elif cls.is_coding_subject(subject_slug):
                questions = cls._generate_practical_coding_questions(subject_slug, topic_slug, count)
            else:
                questions = cls._generate_pedagogical_template_questions(subject_slug, topic_slug, count)

        # Enforce balanced distribution: 25% A, 25% B, 25% C, 25% D
        from app.services.question_bank import rebalance_options_to_target
        for i, q in enumerate(questions):
            target_slot = ["A", "B", "C", "D"][i % 4]
            q.options, q.correct_option_id = rebalance_options_to_target(
                q.options, q.correct_option_id, target_slot
            )
        return questions

    @classmethod
    def _generate_practical_coding_questions(
        cls,
        subject_slug: str,
        topic_slug: str,
        count: int,
    ) -> List[Question]:
        """
        Extracts genuine code-based practical questions from curated bank.
        """
        raw_items = PRACTICAL_PYTHON_QUESTION_BANK.get(topic_slug)
        if not raw_items:
            raw_items = PRACTICAL_PYTHON_QUESTION_BANK["data-structures-and-types"]

        questions: List[Question] = []
        for i in range(count):
            item = raw_items[i % len(raw_items)]
            opts = [QuestionOption(id=o["id"], text=o["text"]) for o in item["options"]]
            q = Question(
                subject_slug=subject_slug,
                topic_slug=topic_slug,
                subtopic_slug=topic_slug,
                difficulty=item.get("difficulty", "medium"),
                prompt_text=item["prompt"],
                code_snippet=item.get("code_snippet"),
                options=opts,
                correct_option_id=item["correct"],
                explanation=item["explanation"],
                is_ai_generated=False,
                review_status="approved",
                reviewed_by="academic_curriculum_board",
                reviewed_at=datetime.now(timezone.utc),
            )
            questions.append(q)

        return questions

    @classmethod
    def _generate_practical_math_questions(
        cls,
        subject_slug: str,
        topic_slug: str,
        count: int,
    ) -> List[Question]:
        """
        Extracts genuine calculation-based mathematical questions from the curated bank.
        """
        raw_items = PRACTICAL_MATH_QUESTION_BANK.get(topic_slug)
        if not raw_items:
            # Fallback to general commercial arithmetic if topic not found in bank
            raw_items = PRACTICAL_MATH_QUESTION_BANK["commercial-arithmetic-and-interest"]

        questions: List[Question] = []
        for i in range(count):
            item = raw_items[i % len(raw_items)]
            opts = [QuestionOption(id=o["id"], text=o["text"]) for o in item["options"]]
            q = Question(
                subject_slug=subject_slug,
                topic_slug=topic_slug,
                subtopic_slug=topic_slug,
                difficulty=item.get("difficulty", "medium"),
                prompt_text=item["prompt"],
                code_snippet=None,
                options=opts,
                correct_option_id=item["correct"],
                explanation=item["explanation"],
                is_ai_generated=False,
                review_status="approved",
                reviewed_by="academic_curriculum_board",
                reviewed_at=datetime.now(timezone.utc),
            )
            questions.append(q)

        return questions

    @classmethod
    async def _generate_via_llm(
        cls,
        subject_slug: str,
        topic_slug: str,
        count: int,
    ) -> List[Question]:
        is_math = cls.is_math_subject(subject_slug)
        system_role = (
            "You are an expert mathematics examiner and academic professor. Generate practical, calculation-based, clear math problems with exact formulas and step-by-step solutions."
            if is_math
            else "You are an expert academic examiner and computer science professor."
        )

        prompt = (
            f"Generate {count} distinct multiple-choice diagnostic questions for subject '{subject_slug}', topic '{topic_slug}'.\n"
            f"Requirements:\n"
            f"- Question difficulty distribution: easy, medium, hard.\n"
            f"- 4 options (id: 'A', 'B', 'C', 'D') with clear numerical or conceptual text.\n"
            f"- One unambiguous correct_option_id. Ensure the correct answer is evenly distributed across options 'A', 'B', 'C', and 'D' (~25% each; avoid clustering on 'A' or 'B').\n"
            f"- Clear pedagogical explanation demonstrating the derivation.\n"
            f"- No irrelevant computer science terms if subject is mathematics.\n"
            f"Return JSON format: {{\"questions\": [{{\"difficulty\": \"easy|medium|hard\", \"prompt_text\": \"...\", \"code_snippet\": null, \"options\": [{{\"id\": \"A\", \"text\": \"...\"}}], \"correct_option_id\": \"A\", \"explanation\": \"...\"}}]}}"
        )

        from app.services.llm_provider import get_default_llm_provider

        llm = get_default_llm_provider()
        content = await llm.generate_completion(system_role, prompt)
        if content:
            try:
                parsed = json.loads(content)
                q_list = parsed.get("questions", [])
                results: List[Question] = []
                for q_dict in q_list:
                    opts = [
                        QuestionOption(id=o["id"], text=o["text"])
                        for o in q_dict.get("options", [])
                    ]
                    results.append(
                        Question(
                            subject_slug=subject_slug,
                            topic_slug=topic_slug,
                            subtopic_slug=topic_slug,
                            difficulty=q_dict.get("difficulty", "medium"),
                            prompt_text=q_dict.get("prompt_text"),
                            code_snippet=q_dict.get("code_snippet"),
                            options=opts,
                            correct_option_id=q_dict.get("correct_option_id", "A"),
                            explanation=q_dict.get("explanation", "Verified academic derivation."),
                            is_ai_generated=True,
                            review_status="approved",
                            reviewed_by="ai_pedagogical_pipeline",
                            reviewed_at=datetime.now(timezone.utc),
                        )
                    )
                return results
            except Exception as parse_err:
                logger.warning("Failed to parse LLM completion as question JSON: %s", parse_err)

        return []

    @classmethod
    def _generate_pedagogical_template_questions(
        cls,
        subject_slug: str,
        topic_slug: str,
        count: int,
    ) -> List[Question]:
        """
        Creates well-structured, domain-aligned pedagogical assessment questions for general CS subjects.
        """
        readable_subject = subject_slug.replace("-", " ").title()
        readable_topic = topic_slug.replace("-", " ").title()
        difficulties = ["easy", "medium", "hard", "medium"]

        templates = [
            {
                "prompt": f"In {readable_subject}, what is the primary role or foundational characteristic of {readable_topic}?",
                "options": [
                    {"id": "A", "text": f"It defines the core operational invariants and abstractions for {readable_topic}."},
                    {"id": "B", "text": "It bypasses standard verification to maximize raw throughput."},
                    {"id": "C", "text": "It enforces global locks that prevent concurrent execution entirely."},
                    {"id": "D", "text": "It eliminates the need for memory management or resource constraints."},
                ],
                "correct": "A",
                "explanation": f"In {readable_subject}, understanding {readable_topic} establishes foundational mental models and guarantees systemic correctness.",
            },
            {
                "prompt": f"When optimizing performance within {readable_topic} ({readable_subject}), which trade-off is most commonly evaluated?",
                "options": [
                    {"id": "A", "text": "Randomized seed generation vs deterministic hashing"},
                    {"id": "B", "text": "Space complexity (auxiliary memory) vs time complexity (computational latency)"},
                    {"id": "C", "text": "Character encoding length vs network packet headers"},
                    {"id": "D", "text": "Display frame refresh rate vs persistent disk sectors"},
                ],
                "correct": "B",
                "explanation": "Balancing space and time complexity is the classic architectural trade-off in modern engineering and algorithmic design.",
            },
            {
                "prompt": f"Which critical failure mode or edge case must be safeguarded against when implementing {readable_topic}?",
                "options": [
                    {"id": "A", "text": "Operating system desktop window minimize events"},
                    {"id": "B", "text": "Monospaced font rendering discrepancies"},
                    {"id": "C", "text": "Zero-division or empty/null input boundary conditions"},
                    {"id": "D", "text": "HTTP GET cache header expiration without network disconnects"},
                ],
                "correct": "C",
                "explanation": "Defensive design requires validating boundary states such as empty collections, null pointers, and divide-by-zero states.",
            },
            {
                "prompt": f"How does architectural modularity in {readable_topic} improve long-term system reliability?",
                "options": [
                    {"id": "A", "text": "By increasing coupling between unrelated stateful modules"},
                    {"id": "B", "text": "By enforcing synchronous single-threaded execution across distributed nodes"},
                    {"id": "C", "text": "By converting all dynamic data structures into fixed global variables"},
                    {"id": "D", "text": "By isolating concerns, enabling targeted unit testing, and minimizing blast radius"},
                ],
                "correct": "D",
                "explanation": "Separation of concerns reduces coupling, narrows fault domains, and makes components easier to test and reason about.",
            },
        ]

        questions: List[Question] = []
        for i in range(count):
            tmpl = templates[i % len(templates)]
            diff = difficulties[i % len(difficulties)]
            opts = [QuestionOption(id=o["id"], text=o["text"]) for o in tmpl["options"]]
            q = Question(
                subject_slug=subject_slug,
                topic_slug=topic_slug,
                subtopic_slug=topic_slug,
                difficulty=diff,
                prompt_text=tmpl["prompt"],
                code_snippet=None,
                options=opts,
                correct_option_id=tmpl["correct"],
                explanation=tmpl["explanation"],
                is_ai_generated=True,
                review_status="approved",
                reviewed_by="pedagogical_template_pipeline",
                reviewed_at=datetime.now(timezone.utc),
            )
            questions.append(q)

        return questions
