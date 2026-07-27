import io, json, math, os, subprocess, sys, time
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

W, H, FPS = 1920, 1080, 30
OUT = Path("sunway_optimal_route.mp4")
CACHE = Path("map_cache")
CACHE.mkdir(exist_ok=True)

PLACES = [
    ("Sunway University", 3.0674034721956636, 101.60378735581176),
    ("Vidhipriya", 3.0701106184932523, 101.60248765142919),
    ("Wen Li", 3.0824793225352116, 101.62024215387541),
    ("Hui San", 3.153208059162442, 101.59201061372572),
    ("Keertana", 3.019185323436898, 101.53638294969723),
    ("Qi Yung", 3.01228518212335, 101.42828808653051),
]
COLORS = {"nav": (20, 78, 145), "green": (24, 145, 82), "red": (198, 52, 62)}
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "RouteVideoRenderer/1.0 (educational animation)"
TILE_MEM = {}
MAP_MEM = {}

def font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F18, F22, F26, F32, F40 = font(18), font(22), font(26, True), font(32, True), font(40, True)

def route_cache():
    p = CACHE / "routes.json"
    if p.exists(): return json.loads(p.read_text(encoding="utf-8"))
    routes = []
    for i in range(5):
        a, b = PLACES[i], PLACES[i+1]
        url = (f"https://router.project-osrm.org/route/v1/driving/"
               f"{a[2]},{a[1]};{b[2]},{b[1]}?overview=full&geometries=geojson&steps=false")
        r = SESSION.get(url, timeout=60); r.raise_for_status(); data = r.json()
        if data.get("code") != "Ok": raise RuntimeError(data)
        rt = data["routes"][0]
        routes.append({"coordinates": rt["geometry"]["coordinates"],
                       "distance_m": rt["distance"], "duration_s": rt["duration"]})
        print(f"Fetched route {i+1}: {rt['distance']/1000:.2f} km")
    p.write_text(json.dumps(routes), encoding="utf-8")
    return routes

def world(lon, lat, z):
    n = 256 * (2 ** z)
    x = (lon + 180.0) / 360.0 * n
    lat = max(-85.05112878, min(85.05112878, lat))
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def tile(z, x, y):
    n = 2 ** z; x %= n
    key = (z, x, y)
    if key in TILE_MEM: return TILE_MEM[key]
    p = CACHE / f"tile_{z}_{x}_{y}.png"
    if not p.exists():
        url = f"https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
        r = SESSION.get(url, timeout=40); r.raise_for_status(); p.write_bytes(r.content)
    im = Image.open(p).convert("RGB")
    TILE_MEM[key] = im
    return im

def map_frame(center, zoom):
    # Reuse exact hold/intro frames while retaining continuous camera movement.
    mkey = (round(center[0], 9), round(center[1], 9), round(zoom, 6))
    if mkey in MAP_MEM: return MAP_MEM[mkey][0].copy(), MAP_MEM[mkey][1]
    z = max(0, min(18, int(math.ceil(zoom))))
    scale = 2 ** (zoom - z)
    cx, cy = world(center[0], center[1], z)
    left, top = cx - W/(2*scale), cy - H/(2*scale)
    right, bottom = cx + W/(2*scale), cy + H/(2*scale)
    x0, x1 = math.floor(left/256), math.floor(right/256)
    y0, y1 = math.floor(top/256), math.floor(bottom/256)
    base = Image.new("RGB", ((x1-x0+1)*256, (y1-y0+1)*256), "#eef0ed")
    for yy in range(y0, y1+1):
        for xx in range(x0, x1+1):
            base.paste(tile(z, xx, yy), ((xx-x0)*256, (yy-y0)*256))
    crop = base.crop((left-x0*256, top-y0*256, right-x0*256, bottom-y0*256))
    result = crop.resize((W,H), Image.Resampling.BILINEAR), (cx,cy,z,scale)
    if len(MAP_MEM) < 16: MAP_MEM[mkey] = (result[0].copy(), result[1])
    return result

def screen(lon, lat, camera):
    cx,cy,z,s = camera; x,y = world(lon,lat,z)
    return W/2+(x-cx)*s, H/2+(y-cy)*s

def fit_camera(coords, pad=260):
    # Fit in Web Mercator using a stable reference zoom.
    pts = [world(p[0],p[1],16) for p in coords]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    spanx=max(xs)-min(xs); spany=max(ys)-min(ys)
    s=min((W-2*pad)/max(spanx,1), (H-2*pad)/max(spany,1))
    zoom=16+math.log2(s)
    wx=(min(xs)+max(xs))/2; wy=(min(ys)+max(ys))/2
    n=256*2**16; lon=wx/n*360-180
    lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*wy/n))))
    return (lon,lat), max(11.0,min(16.8,zoom))

def ease(t): return t*t*(3-2*t)
def lerp(a,b,t): return a+(b-a)*t

def cumulative(coords):
    d=[0.0]
    for a,b in zip(coords,coords[1:]):
        x1,y1=world(a[0],a[1],16); x2,y2=world(b[0],b[1],16)
        d.append(d[-1]+math.hypot(x2-x1,y2-y1))
    return d

def partial(coords, cum, frac):
    target=cum[-1]*frac
    for i in range(1,len(cum)):
        if cum[i]>=target:
            f=(target-cum[i-1])/max(cum[i]-cum[i-1],1e-9)
            q=(lerp(coords[i-1][0],coords[i][0],f),lerp(coords[i-1][1],coords[i][1],f))
            return coords[:i]+[q],q
    return coords,coords[-1]

def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)

def marker(im, xy, label, state, special=""):
    x,y=xy; glow=Image.new("RGBA",im.size,(0,0,0,0)); gd=ImageDraw.Draw(glow)
    col=COLORS["green"] if state=="visited" else COLORS["red"]
    gd.ellipse((x-26,y-26,x+26,y+26), fill=col+(65,))
    glow=glow.filter(ImageFilter.GaussianBlur(14)); im.alpha_composite(glow)
    d=ImageDraw.Draw(im); d.ellipse((x-14,y-14,x+14,y+14),fill=col+(255,),outline="white",width=4)
    if state=="visited":
        d.line((x-6,y,x-1,y+6,x+8,y-6),fill="white",width=4,joint="curve")
    text=label + ("  •  "+special if special else "")
    bb=d.textbbox((0,0),text,font=F22); tw=bb[2]-bb[0]
    bx=max(18,min(W-tw-38,x-tw/2-18)); by=y-64
    if by<80: by=y+27
    rounded(d,(bx,by,bx+tw+36,by+38),14,(255,255,255,238),(205,210,214,255),2)
    d.text((bx+18,by+7),text,font=F22,fill=(35,39,43,255))

def draw_route(d, pts, color=COLORS["nav"]):
    if len(pts)<2:return
    d.line(pts,fill=(255,255,255,255),width=18,joint="curve")
    d.line(pts,fill=color+(255,),width=11,joint="curve")

def overlay_ui(im, title, subtitle=None):
    d=ImageDraw.Draw(im)
    rounded(d,(32,28,790,104),20,(255,255,255,244),(210,214,218,255),2)
    d.ellipse((56,49,88,81),fill=COLORS["nav"]+(255,)); d.ellipse((66,59,78,71),fill="white")
    d.text((105,48),title,font=F32,fill=(28,32,36,255))
    if subtitle:
        bb=d.textbbox((0,0),subtitle,font=F22); tw=bb[2]-bb[0]
        rounded(d,(32,120,70+tw,168),15,(22,28,34,225))
        d.text((51,132),subtitle,font=F22,fill="white")
    attr="© OpenStreetMap contributors  © CARTO"
    bb=d.textbbox((0,0),attr,font=F18); tw=bb[2]-bb[0]
    rounded(d,(W-tw-32,H-35,W-10,H-7),5,(255,255,255,210))
    d.text((W-tw-22,H-31),attr,font=F18,fill=(80,80,80,255))

def render():
    routes=route_cache(); coords=[r["coordinates"] for r in routes]
    cams=[fit_camera(c,220) for c in coords]
    allcoords=[p for c in coords for p in c]
    finalcam=fit_camera(allcoords,250)
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ffmpeg,"-y","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264",
         "-preset","medium","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    total_frames=int((2.5+5*(4.2+0.8)+3.5)*FPS); done=0

    def emit(center,zoom,completed,active=-1,frac=0,title="A Search Optimal Route*",subtitle=None,moving=False):
        nonlocal done
        bg,cam=map_frame(center,zoom); im=bg.convert("RGBA"); d=ImageDraw.Draw(im)
        for j in range(completed): draw_route(d,[screen(*p,cam) for p in coords[j]])
        node=None
        if active>=0:
            part,node=partial(coords[active],cums[active],frac)
            draw_route(d,[screen(*p,cam) for p in part])
        visited=completed + (1 if active>=0 and frac>=1 else 0)
        for k,(name,lat,lon) in enumerate(PLACES):
            x,y=screen(lon,lat,cam)
            if -100<x<W+100 and -100<y<H+100:
                special="START" if k==0 else ("FINAL" if k==5 else "")
                marker(im,(x,y),name,"visited" if k<=visited else "unvisited",special)
        if moving and node:
            x,y=screen(*node,cam); glow=Image.new("RGBA",im.size,(0,0,0,0)); gd=ImageDraw.Draw(glow)
            gd.ellipse((x-28,y-28,x+28,y+28),fill=(40,145,255,105)); glow=glow.filter(ImageFilter.GaussianBlur(13)); im.alpha_composite(glow)
            d=ImageDraw.Draw(im); d.ellipse((x-11,y-11,x+11,y+11),fill=(40,145,255,255),outline="white",width=4)
        overlay_ui(im,title,subtitle)
        proc.stdin.write(np.asarray(im.convert("RGB"),dtype=np.uint8).tobytes()); done+=1
        if done%90==0: print(f"Rendered {done}/{total_frames} frames")

    cums=[cumulative(c) for c in coords]
    # Intro overview.
    for f in range(int(2.5*FPS)):
        emit(finalcam[0],finalcam[1],0,title="A Search Optimal Route*")
    prev=finalcam
    for i in range(5):
        center,zoom=cams[i]
        subtitle=f"Iteration {i+1}: {PLACES[i][0]} → {PLACES[i+1][0]}"
        moveframes=int(4.2*FPS)
        for f in range(moveframes):
            t=f/(moveframes-1); pan=ease(min(1,t/0.18))
            cc=(lerp(prev[0][0],center[0],pan),lerp(prev[0][1],center[1],pan)); zz=lerp(prev[1],zoom,pan)
            emit(cc,zz,i,i,ease(t),subtitle=subtitle,moving=True)
        for _ in range(int(.8*FPS)): emit(center,zoom,i+1,subtitle=subtitle)
        prev=(center,zoom)
    # Final smooth pullback and hold.
    finalframes=int(3.5*FPS)
    for f in range(finalframes):
        t=ease(min(1,f/(1.6*FPS))); cc=(lerp(prev[0][0],finalcam[0][0],t),lerp(prev[0][1],finalcam[0][1],t)); zz=lerp(prev[1],finalcam[1],t)
        emit(cc,zz,5,title="Goal Reached — All Five Residences Visited")
    proc.stdin.close(); rc=proc.wait()
    if rc: raise RuntimeError(f"ffmpeg exited {rc}")
    print(f"Created {OUT.resolve()}")

if __name__=="__main__": render()
