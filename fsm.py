from transitions.extensions import GraphMachine
import requests
from bs4 import BeautifulSoup 
from utils import send_text_message,send_image_url
import random
# depaat_code={
#     "體育室":"A2","軍訓室":"A3","師培中心":"A4","計網中心":"A5","服務學習":"A6","共同英授":"AA","華語中心":"AH","不分系學程":"AN","外語中心":"A1","通識中心":"A9","公民歷史":"AG","基礎國文":"A7",
#     "文學院學士班":"B0","中文系":"B1",
# }
class TocMachine(GraphMachine):
    depart_code=""
    course_name=""
    state2_to_state1=False
    show_fsm_to_user=False
    ans=0
    up_limit=100
    low_limit=0
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    def is_going_to_user(self,event):
        text = event.message.text
        return text.lower() == "restart"
    
    def on_enter_user(self,event):
        print("I'm entering user from state1")
        reply_token = event.reply_token
        self.low_limit=0
        self.up_limit=100
        self.ans=0
        try:
            send_text_message(reply_token, "請輸入系所代號 or show fsm")
        except:
            return
    def on_exit_user(self,event=None):
        print("leaving user")
    
    def is_going_to_state1(self, event):
        text = event.message.text
        self.depart_code=text
        if(text!="show fsm"):
            if(text!="restart"):
                return True
    def on_enter_state1(self, event):
        if(self.state2_to_state1):
            print("I'm back from state2")
            self.state2_to_state1=False
            return
        print("I'm entering state1 from user")
        reply_token = event.reply_token
        send_text_message(reply_token, "請輸入課程名稱 ")
    def on_exit_state1(self,event=None):
        print("Leaving state1")
  
    def is_going_to_state2(self, event):
        text = event.message.text
        self.course_name=text
        if(text!="restart"):
            return True
        else:
            return False
    def on_enter_state2(self, event):
        print("I'm entering state2")
        reply_token = event.reply_token

        url="http://course-query.acad.ncku.edu.tw/qry/qry001.php?dept_no="+self.depart_code
        res=requests.get(url)
        res.encoding='utf-8'

        soup=BeautifulSoup(res.text,"html.parser")
        temp=[]
        for link in soup.find_all("tr"):
            #print(link.find("span","dept_name").text)
            temp2=[]
            coures=link.find_all("td")
            for info in coures:
                #print(info.text)
                if(info.text!=""):
                    temp2.append(info.text.replace("\n","").replace("\t",""))
                else:
                    temp2.append(" ")
            href=link.find("a" ,"course_full_name")
            if(href):
                #print(href['href'])
                temp2.append(href['href'])
            else:
                temp2.append("no course website")
            temp.append(temp2)
        result=""
        for i in temp:
            if(len(i)>13):
                if(i[11]==self.course_name):
                    result+=i[11]+"\n"+"教師名稱: "+i[14]+"\n"+"系號:"+i[1]+"序號:"+i[2]+"\n"+"學分數:"+i[13]+"\n"+"時間: "+i[17]+"\n"+"已選課人數:"+i[15]+" 餘額:"+i[16]+"\n"+"課程地圖連結:\n"+i[26]+"\n"
        print(result)
        if(result):
            send_text_message(reply_token,result)
        else:
            send_text_message(reply_token,"查無此課程")
        self.state2_to_state1=True
        self.go_back_state1(event)
    def on_exit_state2(self,event=None):
        print("Leaving state2")

    def is_going_to_show_fsm(self,event):
        text = event.message.text
        return text.lower() == "show fsm"
    def on_enter_show_fsm(self,event):
        print("I'm entering show fsh")
        reply_token = event.reply_token
        #send_image_url(reply_token, "https://66b8faa7.ngrok.io/show-fsm")
        self.ans=random.randint(0,100)
        print("答案:",self.ans)
        send_text_message(reply_token,"請從0~100猜一個數字")
        self.show_fsm_to_user=True
        # self.go_back_user(event)
    def on_exit_show_fsm(self,event=None):
        print("exit show_fsm")

    def is_going_to_smaller(self,event):
        text = event.message.text
        try:
            self.guess=int(text)
        except:
            return
        return int(text)<self.ans
    def on_enter_smaller(self,event):
        print("I'm entering smaller")
        reply_token = event.reply_token
        #send_image_url(reply_token, "https://66b8faa7.ngrok.io/show-fsm")
        self.low_limit=self.guess
        send_text_message(reply_token,"請從"+str(self.low_limit)+"~"+str(self.up_limit)+"猜一個數字")
    def on_exit_smaller(self,event=None):
        print("exit smaller")

    
    def is_going_to_larger(self,event):
        text = event.message.text
        try:
            self.guess=int(text)
        except:
            return
        return int(text) > self.ans
    def on_enter_larger(self,event):
        print("I'm entering larger")
        reply_token = event.reply_token
        self.up_limit=self.guess
        send_text_message(reply_token,"請從"+str(self.low_limit)+"~"+str(self.up_limit)+"猜一個數字")
        self.show_fsm_to_user=True
        # self.go_back_user(event)
    def on_exit_larger(self,event=None):
        print("exit larger")


    def is_going_to_equal(self,event):
        text = event.message.text
        try:
            self.guess=int(text)
        except:
            return
        return int(text) == self.ans
    def on_enter_equal(self,event):
        print("I'm entering equal")
        reply_token = event.reply_token
        self.low_limit=self.guess
        #send_text_message(reply_token,"答案正確")
        send_image_url(reply_token, "https://f74064070toc.herokuapp.com/show-fsm")
        self.show_fsm_to_user=True
        self.go_back_user(event)
    def on_exit_equal(self,event=None):
        print("exit equal")
    def restart(self,event):
        text = event.message.text
        return text.lower()=="restart"