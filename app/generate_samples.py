import os
from PIL import Image, ImageDraw, ImageFont

def generate_test_upload_samples():
    """Generates authentic sample images for users to drag/drop or click to test the + upload feature."""
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "samples")
    os.makedirs(samples_dir, exist_ok=True)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 22)
        font_h2 = ImageFont.truetype("arialbd.ttf", 15)
        font_body = ImageFont.truetype("arial.ttf", 13)
        font_body_bold = ImageFont.truetype("arialbd.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_h2 = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_body_bold = ImageFont.load_default()

    # 1. 1948 Handwritten Ryotwari Deed (78 Years Old - triggers Human In The Loop)
    img1 = Image.new("RGB", (850, 1100), color=(243, 233, 210))
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([(15, 15), (835, 1085)], outline=(115, 75, 40), width=2)
    d1.text((180, 40), "MADRAS PRESIDENCY - REVENUE SETTLEMENT (1948)", fill=(90, 50, 20), font=font_title)
    d1.text((220, 80), "RYOTWARI PATTA / பட்டா உறுதி பத்திரம் (FASLI 1358)", fill=(60, 35, 15), font=font_h2)
    d1.line([(30, 115), (820, 115)], fill=(120, 80, 40), width=2)

    y = 140
    lines1 = [
        ("Village / கிராமம்:", "Anamalai (ஆனைமலை)"),
        ("Taluk / தாலுக்கா:", "Pollachi (பொள்ளாச்சி)"),
        ("District / ஜில்லா:", "Coimbatore (கோயம்புத்தூர்)"),
        ("Survey No / புல எண்:", "142/3A"),
        ("Ryot Name / பட்டாதாரர்:", "Ramasamy Gounder (ராமசாமி கவுண்டர்)"),
        ("Father's Name:", "Maruthamuthu Gounder"),
        ("Extent / விஸ்தீரணம்:", "3 Acres 58 Cents (Dry / புஞ்சை)"),
        ("Statute Reference:", "Madras Estates (Abolition & Conversion into Ryotwari) Act XXVI of 1948"),
        ("Assessment / தீStatus:", "Rs. 4 Annas 8 per Fasli year"),
        ("North Boundary:", "Survey No 141 Cart Track (வண்டிப் பாதை)"),
        ("South Boundary:", "Survey No 145 Subramanian Land"),
        ("East Boundary:", "Odai / Drainage Channel"),
        ("West Boundary:", "Survey No 142/2 Murugan Land")
    ]
    for lbl, val in lines1:
        d1.text((50, y), lbl, fill=(90, 50, 20), font=font_body_bold)
        d1.text((320, y), val, fill=(45, 30, 15), font=font_body)
        y += 35

    # Simulated signature and revenue stamp
    d1.rectangle([(620, y + 20), (780, y + 140)], outline=(140, 50, 30), width=2)
    d1.text((640, y + 70), "STAMP ONE ANNA\nCOURT FEE", fill=(140, 50, 30), font=font_body_bold)
    d1.text((50, y + 120), "Signed by: Tahsildar & Settlement Officer, Pollachi Division", fill=(90, 50, 20), font=font_body)
    img1.save(os.path.join(samples_dir, "sample_1948_ryotwari_handwritten.jpg"), quality=90)

    # 2. 1968 Faded Inam Settlement Document (58 Years Old)
    img2 = Image.new("RGB", (850, 1100), color=(240, 235, 218))
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([(15, 15), (835, 1085)], outline=(100, 80, 60), width=2)
    d2.text((170, 40), "GOVERNMENT OF TAMIL NADU - REVENUE DEPARTMENT (1968)", fill=(80, 60, 40), font=font_title)
    d2.text((230, 80), "SETTLEMENT PATTA / சான்றிதழ் எண்: 1968/TK-88", fill=(50, 40, 30), font=font_h2)
    d2.line([(30, 115), (820, 115)], fill=(100, 80, 60), width=2)

    y = 140
    lines2 = [
        ("Village / கிராமம்:", "Swamimalai (சுவாமிமலை)"),
        ("Taluk / வட்டம்:", "Kumbakonam (கும்பகோணம்)"),
        ("District / மாவட்டம்:", "Thanjavur (தஞ்சாவூர்)"),
        ("Survey No / புல எண்:", "88/1B2"),
        ("Landholder / பட்டாதாரர்:", "Kandasamy Pillai (கந்தசாமி பிள்ளை)"),
        ("Extent / பரப்பு:", "2 Acres 03 Cents (Wet / நஞ்சை)"),
        ("Statutory Base:", "Tamil Nadu Land Survey and Boundaries Act 1923 Resurvey"),
        ("Four Boundaries:", "North: Main Road | South: Arasalaru Channel | East: 88/1A | West: Nandavanam")
    ]
    for lbl, val in lines2:
        d2.text((50, y), lbl, fill=(80, 60, 40), font=font_body_bold)
        d2.text((320, y), val, fill=(40, 30, 20), font=font_body)
        y += 40
    d2.text((50, y + 80), "Official Settlement Record - District Collectorate Thanjavur", fill=(80, 60, 40), font=font_body)
    img2.save(os.path.join(samples_dir, "sample_1968_faded_document.jpg"), quality=90)

    # 3. 2022 Modern Digital Computerized Patta (4 Years Old - AI First Automated)
    img3 = Image.new("RGB", (850, 1100), color=(252, 253, 255))
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([(15, 15), (835, 1085)], outline=(30, 58, 138), width=3)
    d3.text((150, 40), "GOVERNMENT OF TAMIL NADU - ANYTIME ANYWHERE e-SERVICES", fill=(30, 58, 138), font=font_title)
    d3.text((250, 80), "COMPUTERIZED EXTRACT FROM 'A' REGISTER & PATTA CHITTA", fill=(15, 23, 42), font=font_h2)
    d3.line([(30, 115), (820, 115)], fill=(30, 58, 138), width=2)

    y = 140
    lines3 = [
        ("District / மாவட்டம்:", "Kanchipuram (காஞ்சிபுரம்)"),
        ("Taluk / வட்டம்:", "Sriperumbudur (ஸ்ரீபெரும்புதூர்)"),
        ("Revenue Village / வருவாய் கிராமம்:", "Sunguvarchatram (சுங்குவார்சத்திரம்)"),
        ("Patta Number / பட்டா எண்:", "5892"),
        ("Survey & Sub-division / புல எண்:", "210/4C"),
        ("Owner Name / உரிமையாளர்:", "Kavitha Sundaram (கவிதா சுந்தரம்)"),
        ("Husband's Name:", "Sundaramurthy"),
        ("Classification / வகைப்பாடு:", "Dry (Punjai / ரயத்துவாரி புஞ்சை)"),
        ("Extent / விஸ்தீரணம்:", "0 Hectares 40.5 Ares (1 Acre 00 Cents)"),
        ("Assessment / தீStatus:", "Rs. 12.50 per annum"),
        ("Statute:", "Tamil Nadu Patta Pass Book Act 1983 (Act 4 of 1986)")
    ]
    for lbl, val in lines3:
        d3.text((50, y), lbl, fill=(30, 58, 138), font=font_body_bold)
        d3.text((350, y), val, fill=(15, 23, 42), font=font_body)
        y += 35

    d3.rectangle([(50, y + 30), (800, y + 110)], outline=(14, 165, 233), width=1)
    d3.text((70, y + 45), "Note: This is a system-generated electronic document as per Section 6 of TN Act 4 of 1986.", fill=(71, 85, 105), font=font_body)
    d3.text((70, y + 75), "Security validation digitally backed by State Land Records Database.", fill=(71, 85, 105), font=font_body)

    img3.save(os.path.join(samples_dir, "sample_2022_digital_patta.jpg"), quality=90)
    print("[Samples] Created 3 sample test documents in static/samples/")

if __name__ == "__main__":
    generate_test_upload_samples()
