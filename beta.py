import logging
import os
import time
from openai import OpenAI
from openai import APIConnectionError, APIError, RateLimitError

# Configure clients with timeout settings
Formator_Client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="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",
    timeout=60.0,  # 60 second timeout
    max_retries=3
)

Prover_Client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="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",
    timeout=60.0,  # 60 second timeout
    max_retries=3
)

Problem = """Prove the Central Limit Theorem: Let $X_1, X_2, \\dots, X_n$ be independent and 
identically distributed (i.i.d.) random variables with mean $\\mu$ and variance $\\sigma^2 < 
\\infty$. Then, as $n \\to \\infty$,
\\[
\\frac{\\overline{X}_n - \\mu}{\\sigma / \\sqrt{n}} \\xrightarrow{d} N(0,1),
\\]
where $\\overline{X}_n = \\frac{1}{n}\\sum_{i=1}^n X_i$ is the sample mean."""

def formator(problem:str = Problem) -> str:
    prompt = "Please autoformalize the following problem(containing Latex) in Lean 4 with a header. Use the following theorem names:.\n\n"
    prompt += problem

    messages = [
        {"role": "system", "content": "You are an expert in mathematics and Lean 4."},
        {"role": "user", "content": prompt}
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            completion = Formator_Client.chat.completions.create(
                model="AI-MO/Kimina-Autoformalizer-7B:featherless-ai",
                messages=messages
            )
            rslt = completion.choices[0].message.content
            logging.info(f"Formator result: {rslt}")
            return rslt if rslt else "formalize failed"
        
        except APIConnectionError as e:
            logging.error(f"Connection error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Max retries reached for formator. Connection failed.")
                return "formalize failed - connection error"
        
        except RateLimitError as e:
            logging.error(f"Rate limit error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)  # Wait longer for rate limits
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Max retries reached for formator. Rate limited.")
                return "formalize failed - rate limited"
        
        except APIError as e:
            logging.error(f"API error on attempt {attempt + 1}: {e}")
            return f"formalize failed - API error: {e}"
        
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            return f"formalize failed - unexpected error: {e}"
    
    return "formalize failed"

def prove(formal_statement: str)->str:
    prompt = "Think about and solve the following problem step by step in Lean 4."
    prompt += f"\n# Formal statement of the problem:\n```lean4\n{formal_statement}\n```\n"
    messages = [
        {"role": "system", "content": "You are an expert in mathematics and proving theorems in Lean 4."},
        {"role": "user", "content": prompt}
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            completion = Prover_Client.chat.completions.create(
                model="AI-MO/Kimina-Prover-Distill-8B:featherless-ai",
                messages=messages
            )
            rslt = completion.choices[0].message.content
            logging.info(f"Prover result: {rslt}")
            return rslt if rslt else "proof failed"
        
        except APIConnectionError as e:
            logging.error(f"Connection error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Max retries reached for prover. Connection failed.")
                return "proof failed - connection error"
        
        except RateLimitError as e:
            logging.error(f"Rate limit error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)  # Wait longer for rate limits
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Max retries reached for prover. Rate limited.")
                return "proof failed - rate limited"
        
        except APIError as e:
            logging.error(f"API error on attempt {attempt + 1}: {e}")
            return f"proof failed - API error: {e}"
        
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            return f"proof failed - unexpected error: {e}"
    
    return "proof failed"

def test_connection():
    """Test if we can connect to the Hugging Face API"""
    try:
        # Simple test with minimal request
        test_messages = [{"role": "user", "content": "Hello"}]
        response = Formator_Client.chat.completions.create(
            model="AI-MO/Kimina-Autoformalizer-7B:featherless-ai",
            messages=test_messages,
            max_tokens=1
        )
        logging.info("Connection test successful")
        return True
    except Exception as e:
        logging.error(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    formalized_problem = formator()
    print("Formalized Problem:\n", formalized_problem)
    
    if "failed" not in formalized_problem.lower():
        logging.info("Starting proof generation...")
        proof_result = prove(formalized_problem)
        print("Proof Result:\n", proof_result)
    else:
        print("Skipping proof generation due to formalization failure.")