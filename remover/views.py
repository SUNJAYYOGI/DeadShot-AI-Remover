import os
import gc
from django.shortcuts import render, redirect 
from django.core.files.base import ContentFile
from rembg import remove
from PIL import Image
import io
from django.http import HttpResponse, Http404
from django.conf import settings
from django.core.files.storage import default_storage

def remove_bg_view(request):
    # 1. Agar request POST hai (Upload)
    if request.method == 'POST' and request.FILES.get('image'):
        input_file = request.FILES['image']
        img = Image.open(input_file)
        output = remove(img)
        
        bio = io.BytesIO()
        output.save(bio, format='PNG')
        
        file_name = f"no_bg_{input_file.name.split('.')[0]}.png"
        path = default_storage.save(f'processed/{file_name}', ContentFile(bio.getvalue()))
        processed_url = default_storage.url(path)

        # 2. URL ko session mein save karega
        request.session['processed_url'] = processed_url
        
        # 3. Page ko Reload hone se rokne ke liye Redirect karega
        return redirect('home') 

    # 4. Agar request GET hai (Page Load/Refresh)
    processed_url = request.session.get('processed_url')

    # Check karega ki file abhi bhi exist karti hai ya delete ho gayi?
    if processed_url:
        # URL se file path nikaleinge
        # Example: /media/processed/img.png -> processed/img.png
        relative_path = processed_url.replace(settings.MEDIA_URL, '')
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Agar file delete ho chuki hai (download ke baad), toh session clear ho jayega
        if not os.path.exists(full_path):
            del request.session['processed_url']
            processed_url = None

    return render(request, 'remover/index.html', {'processed_url': processed_url})

def download_and_delete(request, file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, 'processed', file_name)
    
    print("Download request received for:", file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            file_data = f.read()

        response = HttpResponse(file_data, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        try:
            os.remove(file_path)
            print(f"Successfully deleted from Windows: {file_name}")
            
            # Optional: Download ke waqt hi session bhi clear kar deinge taki file save na ho
            if 'processed_url' in request.session:
                del request.session['processed_url']
                
        except Exception as e:
            print(f"Delete Error: {e}")
            gc.collect()
            try:
                os.remove(file_path)
            except:
                pass

        return response
    else:
        raise Http404("File not found")