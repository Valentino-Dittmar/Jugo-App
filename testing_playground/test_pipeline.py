from pipeline import run_full_pipeline

# Use an image that already exists in your project (like the one you uploaded before)
image_path = "/Users/pavelakaradzhova/Documents/S4 Group Project/customcomplientrgba.png"
user_color = "#448294"

result, output_path = run_full_pipeline(image_path, user_color)

if result:
    print("✅ Compliant dashboard!")
else:
    print(f"❌ Not compliant — see: {output_path}")
