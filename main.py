import json
import asyncio
import aiohttp
from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter
paipu = 'https://tenhou.net/3/?log=2024022923gm-00b9-0000-ada8090e&tw=1' # a paipu for example 

async def cal_battle(my_paipu):
  pid = my_paipu[26:57]
  seat = int(my_paipu[61])
  data = {}
  pai = "https://tenhou.net/5/mjlog2json.cgi?" + pid
  async with aiohttp.ClientSession() as session:
      async with session.get(pai, timeout = 3, headers={'Accept': 'text/js; charset=utf-8','User-Agent':'test'}) as r:

          if r.status == 200:
            data = json.loads(await r.text())
            print(data)
          else:
            raise Exception("Couldn't fetch paipu, maybe wrong format?")
  p = 4
  east = 1 # = 2 if 東
  if(data['name'][3] == ''):
    p = 3
  if('東' in data['rule']['disp']):
    east = 2
  lst = []
  player_name = data['name'][seat] 
  for j in range(p):
     lst.append([data['name'][j], data['sc'][2*j+1], data['sc'][2*j]] )
  lst.sort(key=lambda x:x[1],reverse=True)
  #print(player_name, lst)
  shanten = Shanten()

  match_count = 0
  agari = 0
  agari_pt = 0
  dealin = 0
  dealin_pt = 0
  noagari = [0, 0] # 流局次數, 流局罰符
  rich = [0] * 7 #立直率	立和率	立銃率	立打點	立銃點	立一發	立巡數
  dama = [0, 0]
  furo = [0] * 5 #率 和率	銃率	打點	銃點
  #agari_size = [0] * 5# [満貫, 跳満, 倍満, 三倍満, 役満]
  agari_type = [0] * 12 # [平和率	斷么率	役牌率	一氣率	對對率 5 染手率 全帶率 三色率	七対率	暗刻率 10 自摸率  嶺上率]
  luck = [0] * 5 
  
  for match in data['log']:
    match_count += 1
    dealer = False
    if(match[0][1] % 4 == seat):
      dealer = True
    riichi = False
    furoed = False
    haipai = match[4 + seat * 3]
    mopai = match[5 + seat * 3]
    dapai = match[6 + seat * 3]
    hpm = ""; hpp = ""; hps = ""; hpz = ""
    for hpai in haipai:
      if(hpai == 51): 
        hpm += '5'
      elif(hpai == 52):
        hpp += '5'
      elif(hpai == 53): 
        hps += '5'
      elif(hpai < 20):
        hpm += str(hpai - 10)
      elif(hpai < 30): 
        hpp += str(hpai - 20)
      elif(hpai < 40):
        hps += str(hpai - 30)
      elif(hpai < 50): 
        hpz += str(hpai - 40)
    hptiles = TilesConverter.string_to_34_array(man=hpm, pin=hpp, sou=hps,honors=hpz)
    hpshanten = shanten.calculate_shanten(hptiles)
    luck[0] += hpshanten
    result = match[16]

    for mo in mopai:
      for key in ['p', 'k', 'c']:
        if (key in str(mo)):
          furoed = True
          
    for jun, da in enumerate(dapai, start=1):
      if ('r' in str(da)):
        riichi = True
        rich[0] += 1
        rich[6] += jun

    if(result[0] == "和了"):
      for res in range(1, len(result), 2):
        dpt = result[res]
        ron = result[res + 1]
        if(dpt[seat] > 0):
          agari += 1
          agari_pt += dpt[seat]
          if(riichi): 
            agari_pt -= 1000
            rich[1] += 1
            rich[3] += dpt[seat] 
          if(furoed):
            furo[1] += 1
            furo[3] += dpt[seat] 
          if((not riichi) and (not furoed)):
            dama[0] += 1
            dama[1] += dpt[seat] 
          for thing in ron:
            things = str(thing)
            if("平和" in things):
              agari_type[0] += 1
            if("断幺" in things):
              agari_type[1] += 1
            if("役牌" in things):
              agari_type[2] += 1
            if("一氣" in things):
              agari_type[3] += 1
            if("対々" in things):
              agari_type[4] += 1
            if("一色" in things):
              agari_type[5] += 1
            if("帯幺" in things):
              agari_type[6] += 1
            if("三色同順" in things):
              agari_type[7] += 1
            if("七対" in things):
              agari_type[8] += 1
            if("暗刻" in things):
              agari_type[9] += 1
            if("門前" in things):
              agari_type[10] += 1
            if("嶺上" in things):
              agari_type[11] += 1
            if("ドラ" in things):
              luck[1] += int(things[-3])
              # over 10 doras
              if(things[-4] == '1'): luck[1] += 10
    
            if("裏ドラ" in things):
              luck[2] += 1
            if("一発" in things):
              rich[5] += 1
              
        if(dpt[seat] < 0):
          cnt = 0
          for people in range(p):
            if(dpt[people] < 0):
              cnt += 1
          if(cnt >= 2): #be tsumo-ed
            if(dealer and dpt[seat] <= -4000):
              luck[3] += 1
              luck[4] -= dpt[seat]
          else:
            if(res == 1): dealin += 1
            dealin_pt -= dpt[seat]
            if(riichi):
              rich[2] += 1
              rich[4] -= dpt[seat]
            if(furoed):
              furo[2] += 1
              furo[4] -= dpt[seat]
    if(result[0] == "流局"):
      noagari[0] += 1
      noagari[1] += result[1][seat]
  #agari, agari_pt, dealin, dealin_pt, rich, dama, furo, agari_type, luck
  print("總局數")
  print(match_count)
  print("和牌次數")
  print(agari)
  print("和牌打點")
  print(agari_pt)
  print("放銃次數")
  print(dealin)
  print("放銃銃點")
  print(dealin_pt)
  print("流局(次數, 罰符)")
  print(noagari)
  print("立直(立直次數/和/銃/和點/銃點/一發/巡數)")
  print(rich)
  print("默聽(和/打點)")
  print(dama)
  print("副露(副露次數/和/銃/和點/銃點)")
  print(furo)
  print("和牌(平/斷/役/一氣/対対/染/全帶/三色/七対/暗刻/門摸/嶺)")
  print(agari_type)
  print("運氣(配牌向聽/和牌寶數/裏寶/被炸數(-40up)/被炸點")
  print(luck)
  
asyncio.run(cal_battle(paipu))
