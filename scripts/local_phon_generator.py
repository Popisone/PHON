import time
from llama_cpp import Llama

print("Loading model...")
llm = Llama(
    model_path="qwen2.5-0.5b-instruct-q4_k_m.gguf",
    n_ctx=1024, # Увеличихме контекста, за да побере примера
    n_threads=8,
    verbose=False
)

# Това е "Few-Shot Prompt" - даваме пример на модела какво искаме
prompt = """You are a PHON compiler. Write photonic code based on the instructions.
Here is an example:
User: Write a PHON program for a photonic link with compression ratio 8.5 and channel bandwidth 27.2 GHz.
Assistant:
medium silicon { temperature: 300K; }
compressor c1 { ratio: 8.5; }
channel ch1 { bandwidth: 27.2 GHz; }
flow main {
    band data = 5 GHz @ phase 0;
    compress(data) at c1 -> compressed;
    transmit(compressed) via ch1 -> received;
    return received;
}

User: Write a PHON program for a photonic link with compression ratio 4 and channel bandwidth 2 GHz.
Assistant:
"""

print("Generating PHON code (CPU only)...")
start_time = time.time()

output = llm(
    prompt,
    max_tokens=200,
    stop=["User:"],
    echo=False,
    temperature=0.1 # Намаляваме креативността, искаме точност
)

end_time = time.time()
generated_text = output['choices'][0]['text']
tokens_generated = output['usage']['completion_tokens']
time_taken = end_time - start_time

print("\n=== GENERATED PHON CODE ===")
print(generated_text)
print("===========================")
print(f"Speed: {tokens_generated / time_taken:.2f} tokens/sec")