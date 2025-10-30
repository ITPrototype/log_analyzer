
from django.shortcuts import render
from django.db.models import Count
from .models import LogEntry
import json

def dashboard(request):
    # Top 10 IPs
    top_ips = LogEntry.objects.values('remote_addr').annotate(count=Count('id')).order_by('-count')[:10]
    # Status distribution
    status_counts = LogEntry.objects.values('status').annotate(count=Count('id')).order_by('-count')
    # Top requested paths
    top_paths = LogEntry.objects.values('request_path').annotate(count=Count('id')).order_by('-count')[:10]

    top_ips_list = list(top_ips)
    status_counts_list = list(status_counts)
    top_paths_list = list(top_paths)

    context = {
        'top_ips': top_ips_list,
        'status_counts': status_counts_list,
        'top_paths': top_paths_list,
        # JSON-safe strings for use in client-side JS
        'top_ips_json': json.dumps(top_ips_list, default=str),
        'status_counts_json': json.dumps(status_counts_list, default=str),
        'top_paths_json': json.dumps(top_paths_list, default=str),
    }
    return render(request, 'index.html', context)



from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadForm
from .parsers import parse_log_line
from .models import LogEntry, Source

def upload_log(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save with commit=False so we can attach a Source (required FK)
            uploaded = form.save(commit=False)
            # Ensure there's at least one Source to associate with uploaded logs.
            # Use a sensible default name; if you have multiple sources you may
            # want to expose selection in the form instead.
            source_obj, _ = Source.objects.get_or_create(name='Uploaded logs')
            uploaded.source = source_obj
            uploaded.save()
            path = uploaded.file.path
            count = 0
            batch = []
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parsed = parse_log_line(line)
                    if not parsed:
                        continue
                    batch.append(LogEntry(
                        source=uploaded.source,
                        remote_addr=parsed['remote_addr'],
                        remote_user=parsed['remote_user'],
                        timestamp=parsed['timestamp'],
                        request_method=parsed['request_method'],
                        request_path=parsed['request_path'][:2000],
                        protocol=parsed['protocol'],
                        status=parsed['status'],
                        body_bytes_sent=parsed['body_bytes_sent'],
                        referer=parsed['referer'][:2000] if parsed['referer'] else None,
                        user_agent=parsed['user_agent'][:2000] if parsed['user_agent'] else None,
                        raw_line=parsed['raw_line'][:4000],
                    ))
                    count += 1
                    if len(batch) >= 500:
                        LogEntry.objects.bulk_create(batch)
                        batch = []
                if batch:
                    LogEntry.objects.bulk_create(batch)
            uploaded.processed = True
            uploaded.total_imported = count
            uploaded.save()
            messages.success(request, f"Successfully imported {count} entries.")
            return redirect('index')
    else:
        form = UploadForm()
    return render(request, 'upload.html', {'form': form})
