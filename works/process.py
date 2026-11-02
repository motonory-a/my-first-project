# 作品ギャラリー: works/upload/ に置かれた写真を、軽い画像に変換して works.json に追加する
import json, os, re, hashlib, datetime
from PIL import Image, ImageOps, ImageEnhance
import numpy as np
def enh(im):
    # 明るめの発色に整える(中間調を持ち上げ、少し鮮やかに)
    a=np.asarray(im).astype(float)/255; im=Image.fromarray(((a**0.85)*255).clip(0,255).astype('uint8'))
    im=ImageEnhance.Brightness(im).enhance(1.04); im=ImageEnhance.Contrast(im).enhance(1.06)
    im=ImageEnhance.Color(im).enhance(1.15)
    # 作品集全体の明るさをそろえる(中央値の明るさを0.84に合わせる)
    import math
    m=float(np.median(np.asarray(im.convert('L').resize((256,256))).astype(float)/255))
    if 0.02<m<0.98:
        g=min(max(math.log(0.843)/math.log(m),0.6),1.6)
        im=Image.fromarray(((np.asarray(im).astype(float)/255)**g*255).clip(0,255).astype('uint8'))
    return im
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception: pass
ROOT=os.path.dirname(os.path.abspath(__file__)); UP=os.path.join(ROOT,'upload'); OUT=os.path.join(ROOT,'img'); JS=os.path.join(ROOT,'works.json')
os.makedirs(OUT,exist_ok=True)
data=json.load(open(JS,encoding='utf-8')) if os.path.exists(JS) else []
def title_of(fn):
    t=os.path.splitext(fn)[0]
    if re.match(r'^(IMG|DSC|PXL|LINE|image|Screenshot|スクリーンショット|写真)[\W_]*\d*',t,re.I) or re.fullmatch(r'[\d_\- ]+',t): return ''
    return re.sub(r'[_]+',' ',t).strip()
added=0
for fn in sorted(os.listdir(UP)):
    p=os.path.join(UP,fn)
    if fn.startswith('.') or not os.path.isfile(p): continue
    try:
        im=enh(ImageOps.exif_transpose(Image.open(p)).convert('RGB'))
    except Exception as e:
        print('skip',fn,e); continue
    h=hashlib.sha1(open(p,'rb').read()).hexdigest()[:10]
    if not any(w['id']==h for w in data):
        big=im.copy(); big.thumbnail((1200,1200)); big.save(os.path.join(OUT,h+'.webp'),'WEBP',quality=82,method=6)
        w,hh=im.size; s=min(w,hh); sq=im.crop(((w-s)//2,(hh-s)//2,(w-s)//2+s,(hh-s)//2+s)).resize((480,480),Image.LANCZOS)
        sq.save(os.path.join(OUT,h+'_t.webp'),'WEBP',quality=80,method=6)
        data.insert(0,{'id':h,'img':'works/img/'+h+'.webp','thumb':'works/img/'+h+'_t.webp','title':title_of(fn),'date':datetime.date.today().isoformat()})
        added+=1
    os.remove(p)
json.dump(data,open(JS,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
# 作品ごとのリンク用ページ(LINEで送ったときに写真が出るように)
OG=os.path.join(ROOT,'og'); PG=os.path.join(ROOT,'p'); os.makedirs(OG,exist_ok=True); os.makedirs(PG,exist_ok=True)
BASE='https://motonory-a.github.io/my-first-project/'
for w in data:
    h=w['id']; jp=os.path.join(OG,h+'.jpg')
    if not os.path.exists(jp):
        try:
            im=Image.open(os.path.join(ROOT,'img',h+'.webp')).convert('RGB'); im.thumbnail((1200,1200)); im.save(jp,'JPEG',quality=85)
        except Exception as e: print('og skip',h,e); continue
    pp=os.path.join(PG,h+'.html')
    if not os.path.exists(pp):
        open(pp,'w',encoding='utf-8').write(f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>オーダーメイドの天然石ブレスレット｜アッキーの作品</title>
<meta property="og:type" content="website"><meta property="og:title" content="この作品のような感じで作りたい"><meta property="og:description" content="アッキーがオーダーメイドでお作りした天然石ブレスレットです。">
<meta property="og:image" content="{BASE}works/og/{h}.jpg"><meta property="og:url" content="{BASE}works/p/{h}.html"><meta name="twitter:card" content="summary_large_image">
<meta http-equiv="refresh" content="0;url=../../?w={h}"></head><body style="margin:0;background:#FBF6F7"><a href="../../?w={h}"><img src="../og/{h}.jpg" alt="作品" style="display:block;max-width:100%;margin:auto"></a></body></html>""")

print('added',added,'total',len(data))
