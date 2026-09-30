import os,json,time
import tkinter as tk
from tkinter import ttk,messagebox
from datetime import date

from tkcalendar import DateEntry

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter,MaxNLocator

APP_TITLE="Expenses Tracker"
DATA_FILE="expenses_data.json"

BG="#0F172A";CARD="#111C33";CARD2="#152343";TEXT="#E5E7EB";MUTED="#94A3B8"
LINE="#243255";ACCENT="#6366F1";GOOD="#22C55E";WARN="#F59E0B";BAD="#EF4444";ENTRY_BG="#0B1224"

def today_str():return date.today().strftime("%Y-%m-%d")
def ym(s):return (s or today_str())[:7]                       # extrage anul si luna in format YYYY-MM
def nid(p="id"):return f"{p}_{time.time_ns()}"              

def safe_float(x:str)->float:
    s=(x or "").strip().replace(" ","")
    if "," in s and "." in s:
        s=s.replace(".","") if s.rfind(",")>s.rfind(".") else s.replace(",","")
    s=s.replace(",",".")
    return float(s)

def fmt_ron(x:float)->str:
    return f"{x:,.2f}".replace(","," ").replace(".",",")+" RON"

def load_state():
    if not os.path.exists(DATA_FILE):
        return {"expenses":[],"goals":[],"settings":{"budget":0.0}}
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f:return json.load(f)
    except:
        return {"expenses":[],"goals":[],"settings":{"budget":0.0}}

def save_state(st):
    tmp=DATA_FILE+".tmp"
    with open(tmp,"w",encoding="utf-8") as f:json.dump(st,f,indent=2,ensure_ascii=False)                # salvare cu variabila tmp ca sa nu corupem fisierul
    os.replace(tmp,DATA_FILE)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE);self.geometry("1100x720");self.configure(bg=BG)

        st=load_state()
        self.expenses=st.get("expenses",[])
        self.goals=st.get("goals",[])
        self.budget=float(st.get("settings",{}).get("budget",0.0))

        self.categories=["Food","Shopping","Divertisment","Transport","Bills","Health","Altele"]
        self.active_month=""

        self._style();self._ui()
        self.refresh_all()
        self.set_status("Ready","info")

    def _style(self):
        s=ttk.Style()                                                           # stilul butoanelor
        try:s.theme_use("clam")
        except:pass
        s.configure("TFrame",background=BG);s.configure("Card.TFrame",background=CARD);s.configure("Card2.TFrame",background=CARD2)
        s.configure("TLabel",background=BG,foreground=TEXT);s.configure("Card.TLabel",background=CARD,foreground=TEXT);s.configure("Muted.TLabel",background=CARD,foreground=MUTED)
        s.configure("TNotebook",background=BG,borderwidth=0);s.configure("TNotebook.Tab",background=CARD2,foreground=TEXT,padding=(12,8))
        s.map("TNotebook.Tab",background=[("selected",CARD)],foreground=[("selected","white")])
        s.configure("TEntry",fieldbackground=ENTRY_BG,foreground=TEXT);s.configure("TCombobox",fieldbackground=ENTRY_BG,foreground=TEXT)
        s.configure("Accent.TButton",background=ACCENT,foreground="white",padding=(12,8));s.map("Accent.TButton",background=[("active","#5457E2")])
        s.configure("Ghost.TButton",background=CARD2,foreground=TEXT,padding=(12,8));s.map("Ghost.TButton",background=[("active","#1B2B4C")])
        s.configure("Treeview",background=CARD,foreground=TEXT,fieldbackground=CARD,rowheight=28,borderwidth=0)
        s.configure("Treeview.Heading",background=CARD2,foreground=TEXT);s.map("Treeview",background=[("selected","#243B72")])

    def persist(self):                                                          # salveaza datele in json
        save_state({"expenses":self.expenses,"goals":self.goals,"settings":{"budget":float(self.budget)}})

    def set_status(self,text,level="info"):
        col={"info":MUTED,"good":GOOD,"warn":WARN,"bad":BAD}.get(level,MUTED)
        self.status.config(text=text,foreground=col)

    def expenses_in_month(self,m):return [e for e in self.expenses if ym(e.get("date"))==m]

    def totals_by_month(self):
        out={}
        for e in self.expenses:
            m=ym(e.get("date"))
            out[m]=out.get(m,0.0)+float(e.get("amount",0))
        return out

    def totals_by_category(self,arr):
        out={}
        for e in arr:
            c=e.get("category") or "Altele"
            out[c]=out.get(c,0.0)+float(e.get("amount",0))
        return out

    def pick_active_month(self):
        months=sorted(self.totals_by_month().keys())
        cur=ym(today_str())
        return cur if cur in months else (months[-1] if months else cur)

    def _ui(self):                                                                                          # interfata grafica
        header=ttk.Frame(self,style="Card2.TFrame");header.pack(fill="x",padx=14,pady=(14,10))
        ttk.Label(header,text="Expenses Tracker",font=("Segoe UI",16,"bold"),
                  background=CARD2,foreground="white").pack(side="left",padx=12,pady=10)
        self.lbl_month=ttk.Label(header,text="",background=CARD2,foreground=MUTED,font=("Segoe UI",10,"bold"))
        self.lbl_month.pack(side="right",padx=12)

        self.nb=ttk.Notebook(self);self.nb.pack(fill="both",expand=True,padx=14,pady=(0,10))
        self.tab_dash=ttk.Frame(self.nb);self.tab_exp=ttk.Frame(self.nb);self.tab_goal=ttk.Frame(self.nb);self.tab_charts=ttk.Frame(self.nb)
        for t,n in [(self.tab_dash,"Dashboard"),(self.tab_exp,"Expenses"),(self.tab_goal,"Savings Goals"),(self.tab_charts,"Charts")]:
            self.nb.add(t,text=n)

        self._dash_ui();self._exp_ui();self._goals_ui();self._charts_ui()

        status=ttk.Frame(self,style="Card2.TFrame");status.pack(fill="x",padx=14,pady=(0,14))
        self.status=ttk.Label(status,text="Ready",background=CARD2,foreground=MUTED,font=("Segoe UI",10))
        self.status.pack(side="left",padx=12,pady=8)

    def _dash_ui(self):
        wrap=ttk.Frame(self.tab_dash);wrap.pack(fill="both",expand=True,padx=10,pady=10)
        left=ttk.Frame(wrap);right=ttk.Frame(wrap)
        left.pack(side="left",fill="both",expand=True,padx=(0,10))
        right.pack(side="right",fill="both",expand=True,padx=(10,0))

        c1=ttk.Frame(left,style="Card.TFrame");c1.pack(fill="x",pady=(0,12))                                                            # total luna activa
        ttk.Label(c1,text="Cheltuieli (luna activă)",style="Card.TLabel",font=("Segoe UI",12,"bold")).pack(anchor="w",padx=14,pady=(12,6))
        self.lbl_total=ttk.Label(c1,text="0,00 RON",style="Card.TLabel",font=("Segoe UI",22,"bold"))
        self.lbl_total.pack(anchor="w",padx=14,pady=(0,12))

        c2=ttk.Frame(left,style="Card.TFrame");c2.pack(fill="x",pady=(0,12))                                                            # buget si progres
        ttk.Label(c2,text="Buget lunar",style="Card.TLabel",font=("Segoe UI",12,"bold")).pack(anchor="w",padx=14,pady=(12,6))

        row=ttk.Frame(c2,style="Card.TFrame");row.pack(fill="x",padx=14,pady=(0,8))
        ttk.Label(row,text="Buget (RON)",style="Card.TLabel").pack(side="left")
        self.ent_budget=ttk.Entry(row,width=14);self.ent_budget.pack(side="left",padx=10)
        self.ent_budget.insert(0,f"{self.budget:.2f}")
        ttk.Button(row,text="Salvează",style="Accent.TButton",command=self.save_budget).pack(side="left")

        self.lbl_budget=ttk.Label(c2,text="",style="Card.TLabel",font=("Segoe UI",11))
        self.lbl_budget.pack(anchor="w",padx=14)
        self.pb=ttk.Progressbar(c2,orient="horizontal",mode="determinate",maximum=100)
        self.pb.pack(fill="x",padx=14,pady=(10,12))

        c3=ttk.Frame(right,style="Card.TFrame");c3.pack(fill="both",expand=True)                                                            # top categorii
        ttk.Label(c3,text="Top categorii",style="Card.TLabel",font=("Segoe UI",12,"bold")).pack(anchor="w",padx=14,pady=(12,8))
        self.top_box=tk.Listbox(c3,bg=CARD,fg=TEXT,highlightthickness=0,bd=0,activestyle="none")
        self.top_box.pack(fill="both",expand=True,padx=14,pady=(0,12))

        foot=ttk.Frame(left,style="Card.TFrame");foot.pack(fill="x")
        ttk.Label(foot,text=f"Salvare: {DATA_FILE}",style="Muted.TLabel").pack(anchor="w",padx=14,pady=(10,12))

    def _exp_ui(self):
        wrap=ttk.Frame(self.tab_exp);wrap.pack(fill="both",expand=True,padx=10,pady=10)

        form=ttk.Frame(wrap,style="Card.TFrame");form.pack(fill="x",pady=(0,12))                        # face butoanele in forma cardului
        ttk.Label(form,text="Adaugă cheltuială",style="Card.TLabel",font=("Segoe UI",12,"bold"))\
            .grid(row=0,column=0,columnspan=6,sticky="w",padx=14,pady=(12,8))

        ttk.Label(form,text="Sumă (RON)",style="Card.TLabel").grid(row=1,column=0,sticky="w",padx=14,pady=6)
        self.ent_amount=ttk.Entry(form,width=14);self.ent_amount.grid(row=2,column=0,sticky="w",padx=14)

        ttk.Label(form,text="Categorie",style="Card.TLabel").grid(row=1,column=1,sticky="w",padx=14,pady=6)
        self.cmb_cat=ttk.Combobox(form,values=self.categories,state="readonly",width=16)
        self.cmb_cat.current(0);self.cmb_cat.grid(row=2,column=1,sticky="w",padx=14)

        ttk.Label(form,text="Dată",style="Card.TLabel").grid(row=1,column=2,sticky="w",padx=14,pady=6)
        self.ent_date=DateEntry(form,width=12,date_pattern="yyyy-mm-dd");self.ent_date.grid(row=2,column=2,sticky="w",padx=14)
        self.ent_date.set_date(date.today())

        ttk.Label(form,text="Notă / Merchant",style="Card.TLabel").grid(row=1,column=3,sticky="w",padx=14,pady=6)
        self.ent_note=ttk.Entry(form,width=30);self.ent_note.grid(row=2,column=3,sticky="w",padx=14)

        ttk.Button(form,text="Adaugă",style="Accent.TButton",command=self.add_expense).grid(row=2,column=4,padx=14)
        ttk.Button(form,text="Refresh",style="Ghost.TButton",command=self.refresh_all).grid(row=2,column=5,padx=6)

        table=ttk.Frame(wrap,style="Card.TFrame");table.pack(fill="both",expand=True)                                # tabel cheltuieli
        ttk.Label(table,text="Cheltuieli",style="Card.TLabel",font=("Segoe UI",12,"bold")).pack(anchor="w",padx=14,pady=(12,8))

        cols=("id","date","category","amount","note")
        self.tree=ttk.Treeview(table,columns=cols,show="headings")
        self.tree.heading("id",text="");self.tree.column("id",width=0,stretch=False)

        for c,t,w,a in [("date","Dată",110,"w"),("category","Categorie",140,"w"),("amount","Sumă",110,"e"),("note","Notă",650,"w")]:
            self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor=a)

        self.tree.pack(fill="both",expand=True,padx=14,pady=(0,10))
        sb=ttk.Scrollbar(table,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set);sb.pack(side="right",fill="y",pady=(0,10))

        act=ttk.Frame(table,style="Card.TFrame");act.pack(fill="x",padx=14,pady=(0,12))
        ttk.Button(act,text="Delete",style="Ghost.TButton",command=self.delete_selected).pack(side="left")
        tk.Button(act,text="Delete all",command=self.delete_all_expenses,bg=BAD,fg="white",bd=0,padx=14,pady=8).pack(side="right")

    def _goals_ui(self):
        wrap=ttk.Frame(self.tab_goal);wrap.pack(fill="both",expand=True,padx=10,pady=10)

        card=ttk.Frame(wrap,style="Card.TFrame");card.pack(fill="x",pady=(0,12))
        ttk.Label(card,text="Savings goals",style="Card.TLabel",font=("Segoe UI",12,"bold"))\
            .grid(row=0,column=0,columnspan=4,sticky="w",padx=14,pady=(12,8))

        ttk.Label(card,text="Nume",style="Card.TLabel").grid(row=1,column=0,sticky="w",padx=14,pady=6)
        self.ent_goal_name=ttk.Entry(card,width=22);self.ent_goal_name.grid(row=2,column=0,sticky="w",padx=14)

        ttk.Label(card,text="Țintă (RON)",style="Card.TLabel").grid(row=1,column=1,sticky="w",padx=14,pady=6)
        self.ent_goal_target=ttk.Entry(card,width=14);self.ent_goal_target.grid(row=2,column=1,sticky="w",padx=14)

        ttk.Button(card,text="Adaugă",style="Accent.TButton",command=self.add_goal).grid(row=2,column=2,sticky="w",padx=14)

        box=ttk.Frame(wrap,style="Card.TFrame");box.pack(fill="both",expand=True)
        ttk.Label(box,text="Obiective",style="Card.TLabel",font=("Segoe UI",12,"bold")).pack(anchor="w",padx=14,pady=(12,8))
        self.goal_list=tk.Listbox(box,bg=CARD,fg=TEXT,highlightthickness=0,bd=0,activestyle="none")
        self.goal_list.pack(fill="both",expand=True,padx=14,pady=(0,10))

        act=ttk.Frame(box,style="Card.TFrame");act.pack(fill="x",padx=14,pady=(0,12))
        ttk.Label(act,text="Contribuție (RON)",style="Card.TLabel").pack(side="left")
        self.ent_goal_add=ttk.Entry(act,width=12);self.ent_goal_add.pack(side="left",padx=10)
        ttk.Button(act,text="Adaugă",style="Ghost.TButton",command=self.goal_contribute).pack(side="left")
        ttk.Button(act,text="Șterge",style="Ghost.TButton",command=self.delete_goal).pack(side="left",padx=10)

    def _charts_ui(self):
        wrap=ttk.Frame(self.tab_charts);wrap.pack(fill="both",expand=True,padx=10,pady=10)
        card=ttk.Frame(wrap,style="Card.TFrame");card.pack(fill="both",expand=True)

        top=ttk.Frame(card,style="Card.TFrame");top.pack(fill="x",padx=14,pady=(12,8))
        ttk.Label(top,text="Charts",style="Card.TLabel",font=("Segoe UI",12,"bold")).pack(side="left")
        ttk.Button(top,text="Refresh",style="Ghost.TButton",command=self.refresh_charts).pack(side="right")

        self.fig=Figure(figsize=(9.6,4.8),dpi=100);self.fig.patch.set_facecolor(CARD)
        self.ax1=self.fig.add_subplot(121);self.ax2=self.fig.add_subplot(122)
        self.canvas=FigureCanvasTkAgg(self.fig,master=card)
        self.canvas.get_tk_widget().pack(fill="both",expand=True,padx=10,pady=(0,12))

    def save_budget(self):                                  # actiuni
        try:
            b=safe_float(self.ent_budget.get().strip())
            if b<0:raise ValueError
        except:
            return messagebox.showerror("Eroare","Buget invalid.")
        self.budget=float(b)
        self.persist();self.refresh_dashboard();self.refresh_charts();self.set_status("Budget saved","good")

    def add_expense(self):
        
        s=self.ent_amount.get().strip()                                             # validare sumă
        if not s:return messagebox.showerror("Eroare","Introdu suma.")
        try:
            amt=safe_float(s)
            if amt<=0:raise ValueError
        except:
            return messagebox.showerror("Eroare","Sumă invalidă.")

        d=self.ent_date.get_date().strftime("%Y-%m-%d")
        note=self.ent_note.get().strip()
        cat=self.cmb_cat.get().strip() or "Altele"

        self.expenses.append({"id":nid("exp"),"date":d,"category":cat,"amount":float(amt),"note":note})         # salvam cheltuiala
        self.persist()

        self.ent_amount.delete(0,tk.END);self.ent_note.delete(0,tk.END)
        self.refresh_all();self.set_status("Saved","good")

    def selected_expense(self):
        sel=self.tree.selection()
        if not sel:return None
        exp_id=self.tree.item(sel[0],"values")[0]
        for e in self.expenses:
            if e.get("id")==exp_id:return e
        return None

    def delete_selected(self):
        e=self.selected_expense()
        if not e:return messagebox.showinfo("Info","Selectează o cheltuială.")
        if not messagebox.askyesno("Confirmare","Ștergi cheltuiala selectată?"):return
        self.expenses=[x for x in self.expenses if x.get("id")!=e.get("id")]
        self.persist();self.refresh_all();self.set_status("Deleted","warn")

    def delete_all_expenses(self):
        if not self.expenses:return messagebox.showinfo("Info","Nu există cheltuieli de șters.")
        if not messagebox.askyesno("Confirmare","Ștergi TOATE cheltuielile?"):return
        self.expenses.clear()
        self.persist();self.refresh_all();self.set_status("Deleted all expenses","warn")

    def add_goal(self):
        name=self.ent_goal_name.get().strip()
        if not name:return messagebox.showerror("Eroare","Introdu nume goal.")
        try:
            tgt=safe_float(self.ent_goal_target.get().strip())
            if tgt<=0:raise ValueError
        except:
            return messagebox.showerror("Eroare","Țintă invalidă.")

        self.goals.append({"id":nid("goal"),"name":name,"target":float(tgt),"saved":0.0})
        self.persist()
        self.ent_goal_name.delete(0,tk.END);self.ent_goal_target.delete(0,tk.END)
        self.refresh_all();self.set_status("Goal added","good")

    def goal_contribute(self):
        sel=self.goal_list.curselection()
        if not sel:return messagebox.showinfo("Info","Selectează un goal.")
        try:
            add=safe_float(self.ent_goal_add.get().strip())
            if add<=0:raise ValueError
        except:
            return messagebox.showerror("Eroare","Contribuție invalidă.")

        g=self.goals[sel[0]]
        g["saved"]=float(g.get("saved",0)+add)
        self.persist()
        self.ent_goal_add.delete(0,tk.END)
        self.refresh_all();self.set_status("Goal updated","good")

    def delete_goal(self):
        sel=self.goal_list.curselection()
        if not sel:return messagebox.showinfo("Info","Selectează un goal.")
        if not messagebox.askyesno("Confirmare","Ștergi goal-ul selectat?"):return
        del self.goals[sel[0]]
        self.persist();self.refresh_all();self.set_status("Goal deleted","warn")

    def refresh_dashboard(self):                                                   # refresh la UI
        m=self.active_month
        cur=self.expenses_in_month(m)
        total=sum(float(e.get("amount",0)) for e in cur)
        self.lbl_total.config(text=fmt_ron(total))

        if self.budget>0:                                                          # progres buget
            pct=max(0,min(100,(total/self.budget)*100))
            self.lbl_budget.config(text=f"{fmt_ron(total)} / {fmt_ron(self.budget)} ({pct:.0f}%)")
            self.pb["value"]=pct
        else:
            self.lbl_budget.config(text="Setează bugetul mai sus.");self.pb["value"]=0

        self.top_box.delete(0,tk.END)               # top categorii
        cats=self.totals_by_category(cur)
        if not cats:self.top_box.insert(tk.END,"Nu există cheltuieli în luna activă.")
        else:
            for c,v in sorted(cats.items(),key=lambda x:x[1],reverse=True)[:8]:
                self.top_box.insert(tk.END,f"{c}: {fmt_ron(v)}")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for e in sorted(self.expenses,key=lambda x:x.get("date",""),reverse=True):
            self.tree.insert("", "end", values=(e.get("id",""),e.get("date",""),e.get("category","Altele"),
                                               f"{float(e.get('amount',0)):.2f}",e.get("note","")))

    def refresh_goals(self):
        self.goal_list.delete(0,tk.END)
        for g in self.goals:
            saved=float(g.get("saved",0));target=float(g.get("target",0))
            pct=0 if target<=0 else (saved/target)*100
            self.goal_list.insert(tk.END,f"{g.get('name','')} — {fmt_ron(saved)} / {fmt_ron(target)} ({pct:.0f}%)")

    def refresh_charts(self):                                           #formeaza graficele
        totals=self.totals_by_month()
        months=sorted(totals.keys())[-6:]

        def kfmt(x,pos=None):
            x=float(x)
            if abs(x)>=10000:return f"{x/1000:.0f}k"
            if abs(x)>=1000:return f"{x/1000:.1f}k"
            return f"{x:.0f}"

        def style_axis(ax):     
            ax.set_facecolor(CARD)
            ax.grid(True,axis="y",color=LINE,alpha=0.35,linewidth=0.8)
            ax.set_axisbelow(True)
            ax.tick_params(axis="x",colors=MUTED);ax.tick_params(axis="y",colors=MUTED)
            ax.yaxis.set_major_formatter(FuncFormatter(kfmt))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
            for s in ("top","right"):ax.spines[s].set_visible(False)
            ax.spines["left"].set_color(LINE);ax.spines["bottom"].set_color(LINE)

        self.ax1.clear();style_axis(self.ax1)           
        if months:
            y=[totals.get(m,0.0) for m in months]
            self.ax1.bar(months,y,width=0.62,color=ACCENT,alpha=0.95)
            self.ax1.plot(months,y,marker="o",linewidth=1.8,alpha=0.55)
            self.ax1.set_title("Total cheltuieli / lună",color=TEXT,fontsize=11,pad=10)
            self.ax1.tick_params(axis="x",labelrotation=35)
            self.ax1.set_ylim(0,max(y)*1.18 if max(y)>0 else 1)
        else:
            self.ax1.text(0.5,0.5,"No data",ha="center",va="center",color=MUTED)
            self.ax1.set_xticks([]);self.ax1.set_yticks([])

        self.ax2.clear();self.ax2.set_facecolor(CARD)       # grafic tip placinta categorii luna activă
        cur=self.expenses_in_month(self.active_month)
        cats=self.totals_by_category(cur)
        if cats:
            vals=list(cats.values());labels=list(cats.keys())
            wedges,texts,autotexts=self.ax2.pie(vals,labels=labels,autopct="%1.0f%%",startangle=90)
            for t in texts:t.set_color(TEXT)
            for at in autotexts:at.set_color(TEXT)
            self.ax2.set_title(f"Categorii ({self.active_month})",color=TEXT,fontsize=11,pad=10)
        else:
            self.ax2.text(0.5,0.5,"No data",ha="center",va="center",color=MUTED)

        try:self.fig.subplots_adjust(wspace=0.25)
        except:pass
        self.canvas.draw()

    def refresh_all(self):
        self.active_month=self.pick_active_month()
        self.lbl_month.config(text=f"Luna activă: {self.active_month}")
        self.refresh_table();self.refresh_goals()
        self.refresh_dashboard();self.refresh_charts()

if __name__=="__main__":
    App().mainloop()