import ctypes
import io
import math
import os
import re
import sys
import time
import tokenize
from pathlib import Path

BASE = Path(__file__).resolve().parent
if os.name == 'nt':
    if (BASE/'tcl'/'tcl8.6'/'init.tcl').is_file():
        os.environ['TCL_LIBRARY']=str(BASE/'tcl'/'tcl8.6')
        os.environ['TK_LIBRARY']=str(BASE/'tcl'/'tk8.6')
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception: pass
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
from engine import plan, LessonError
from samples import SAMPLES

INK='#203D32'; GREEN='#235843'; DARK='#173E32'; MUTE='#526A59'
PAPER='#FFFCF1'; BACK='#F6F5ED'; BORDER='#D9DECD'; WHITE='#FFFFFF'
GOLD='#F5CE6C'; MINT='#E7EEDC'; ERROR='#A23B26'; CODEBG='#FCFDFA'


class Studio:
    def __init__(self, root):
        self.root=root;root.title('小海龟画室')
        self.d=max(.85,min(1.65,root.winfo_fpixels('1i')/96,root.winfo_screenwidth()/940,root.winfo_screenheight()/590))
        self.u=lambda n:round(n*self.d)
        fonts=set(tkfont.families(root))
        self.family=next((f for f in ('Microsoft YaHei UI','Microsoft YaHei','Noto Sans CJK SC','WenQuanYi Zen Hei') if f in fonts),'TkDefaultFont')
        self.mono='Consolas' if 'Consolas' in fonts else 'DejaVu Sans Mono'
        w=min(self.u(1230),root.winfo_screenwidth()-20);h=min(self.u(750),root.winfo_screenheight()-60)
        root.geometry(f'{w}x{h}+{max(0,(root.winfo_screenwidth()-w)//2)}+{max(0,(root.winfo_screenheight()-h)//2-18)}')
        root.minsize(min(w,self.u(810)),min(h,self.u(480)));root.configure(bg=BACK)
        self.pic=BASE/'pictures';self.brand=tk.PhotoImage(file=str(self.pic/'brand.png'))
        if os.name=='nt': root.iconbitmap(str(self.pic/'studio.ico'))
        else: root.iconphoto(True,self.brand)
        size=2 if self.d>=1.5 else 1
        self.sheep=tk.PhotoImage(file=str(self.pic/f'sheep_{size}.png'))
        self.turtles={a:tk.PhotoImage(file=str(self.pic/f'turtle_{size}_{a}.png')) for a in range(0,360,10)}
        self.pending=None;self.resize_id=None;self.after_syntax=None
        self.actions=[];self.count=0;self.progress=0;self.running=False;self.last_line=0
        self.view=(-70.,185.,-166.,52.);self.position=(0,0);self.heading=0.
        self.current=list(SAMPLES)[0];self.snippets={k:v[2] for k,v in SAMPLES.items()}
        self.visibility={k:v[1] for k,v in SAMPLES.items()}
        self.loading=False;self.helpwindow=None;self.step_start=0
        self.build()
        self.load_text(self.snippets[self.current])
        root.after(250,self.run)
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.bind('<F5>',self.run);root.bind('<Control-Return>',self.run)
        root.bind('<Escape>',self.stop);root.bind('<Control-s>',self.save_file)
        root.bind('<Control-o>',self.open_file)

    def font(self,px,bold=False,mono=False):
        return (self.mono if mono else self.family,-self.u(px),'bold' if bold else 'normal')
    def lbl(self,parent,text,px,fg=INK,bg=WHITE,bold=False,**kw):
        return tk.Label(parent,text=text,fg=fg,bg=bg,font=self.font(px,bold),bd=0,**kw)
    def button(self,parent,text,cmd,primary=False):
        bg=GREEN if primary else '#EFF2E9';fg=WHITE if primary else INK
        return tk.Button(parent,text=text,command=cmd,bg=bg,fg=fg,activebackground='#30664D' if primary else '#E0E8D6',
                         activeforeground=fg,disabledforeground='#A2ACA2',relief='flat',bd=0,highlightthickness=0,cursor='hand2',
                         font=self.font(15,True),padx=self.u(15),pady=self.u(6),takefocus=True)

    def build(self):
        u=self.u;root=self.root
        header=tk.Frame(root,bg=DARK);header.pack(fill='x')
        inner=tk.Frame(header,bg=DARK);inner.pack(fill='x',padx=u(23),pady=u(12))
        tk.Label(inner,image=self.brand,bg=MINT,bd=0,padx=2,pady=2).pack(side='left')
        self.lbl(inner,'小海龟画室',25,WHITE,DARK,True).pack(side='left',padx=(u(12),0))
        b=tk.Button(inner,text='指令手册',command=self.help,bg=DARK,fg='#F0F5DE',activebackground=GREEN,activeforeground=WHITE,
                    font=self.font(15),bd=0,highlightthickness=0,cursor='hand2');b.pack(side='right',padx=(u(14),0))
        menu=tk.Menubutton(inner,text='文件 ▾',bg=DARK,fg=WHITE,activebackground=GREEN,activeforeground=WHITE,
                           font=self.font(15),bd=0,highlightthickness=0,cursor='hand2')
        m=tk.Menu(menu,tearoff=False,font=self.font(14));m.add_command(label='打开 Python 代码…',command=self.open_file)
        m.add_command(label='保存当前代码…',command=self.save_file);m.add_separator();m.add_command(label='关于小海龟画室',command=self.about)
        menu['menu']=m;menu.pack(side='right')
        bar=tk.Frame(root,bg=BACK);bar.pack(fill='x',padx=u(23),pady=(u(13),u(12)))
        self.lbl(bar,'课堂示例',15,MUTE,BACK,True).pack(side='left',padx=(0,u(10)))
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('Lesson.TCombobox',fieldbackground=WHITE,background=WHITE,foreground=INK,padding=u(5),arrowsize=u(15))
        style.map('Lesson.TCombobox',fieldbackground=[('readonly',WHITE)],foreground=[('readonly',INK)])
        root.option_add('*TCombobox*Listbox.font',self.font(16))
        self.choice=tk.StringVar(value=self.current)
        box=ttk.Combobox(bar,textvariable=self.choice,values=list(SAMPLES),state='readonly',width=16,style='Lesson.TCombobox',font=self.font(15))
        box.pack(side='left');box.bind('<<ComboboxSelected>>',self.switch)
        self.hint=self.lbl(bar,SAMPLES[self.current][0],15,MUTE,BACK);self.hint.pack(side='left',padx=u(16))
        main=tk.Frame(root,bg=BACK);main.pack(fill='both',expand=True,padx=u(20),pady=(0,u(15)))
        main.grid_rowconfigure(0,weight=1);main.grid_columnconfigure(0,weight=56,uniform='panel')
        main.grid_columnconfigure(1,weight=44,uniform='panel')
        left=tk.Frame(main,bg=WHITE,highlightthickness=1,highlightbackground=BORDER);left.grid(row=0,column=0,sticky='nsew',padx=(0,u(6)))
        right=tk.Frame(main,bg=WHITE,highlightthickness=1,highlightbackground=BORDER);right.grid(row=0,column=1,sticky='nsew',padx=(u(6),0))
        for panel,title in ((left,'画布'),(right,'Python 代码')):
            line=tk.Frame(panel,bg=WHITE);line.pack(fill='x',padx=u(16),pady=u(11))
            self.lbl(line,title,21,INK,WHITE,True).pack(side='left')
            if panel is left:
                self.show_sheep=tk.BooleanVar(value=True)
                cb=tk.Checkbutton(line,text='显示小羊',variable=self.show_sheep,command=self.toggle_sheep,
                                  fg=MUTE,bg=WHITE,activebackground=WHITE,highlightthickness=0,font=self.font(14));cb.pack(side='right')
            else:
                self.lbl(line,'Ctrl + Enter 运行',13,MUTE).pack(side='right')
        self.canvas=tk.Canvas(left,bg=PAPER,bd=0,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True,padx=1);self.canvas.bind('<Configure>',self.resize)
        lf=tk.Frame(left,bg=WHITE);lf.pack(fill='x',padx=u(14),pady=u(10))
        self.coord=self.lbl(lf,'',13,MUTE);self.coord.pack(side='left')
        self.rtlabel=self.lbl(lf,'',13,MUTE);self.rtlabel.pack(side='right')
        edit=tk.Frame(right,bg=CODEBG);edit.pack(fill='both',expand=True,padx=1)
        edit.rowconfigure(0,weight=1);edit.columnconfigure(1,weight=1)
        self.gutter=tk.Canvas(edit,width=u(36),bg='#F0F3EB',highlightthickness=0)
        self.gutter.grid(row=0,column=0,sticky='ns')
        self.editor=tk.Text(edit,wrap='none',undo=True,autoseparators=True,maxundo=120,
            bg=CODEBG,fg=INK,insertbackground=INK,selectbackground='#CFE3B3',
            font=self.font(18,False,True),bd=0,highlightthickness=0,padx=u(8),pady=u(12),
            spacing1=u(3),spacing3=u(3),tabs=(tkfont.Font(font=self.font(18,False,True)).measure('    '),),width=1,height=1)
        self.editor.grid(row=0,column=1,sticky='nsew')
        self.vbar=ttk.Scrollbar(edit,orient='vertical',command=self.editor.yview);self.vbar.grid(row=0,column=2,sticky='ns')
        self.hbar=ttk.Scrollbar(edit,orient='horizontal',command=self.editor.xview);self.hbar.grid(row=1,column=1,sticky='ew')
        self.editor.configure(yscrollcommand=self.scroll_editor,xscrollcommand=self.hbar.set)
        for name,color in [('kw','#80528B'),('num','#A55723'),('str','#326C55'),('comment','#75846E'),('fn','#1E6680')]:
            self.editor.tag_configure(name,foreground=color)
        self.editor.tag_configure('here',background='#E5EED3');self.editor.tag_configure('err',background='#FBE4DA')
        self.editor.tag_raise('sel');self.editor.bind('<<Modified>>',self.modified)
        self.editor.bind('<Configure>',lambda e:self.root.after_idle(self.draw_gutter))
        self.editor.bind('<Tab>',self.indent);self.editor.bind('<Return>',self.newline)
        self.editor.bind('<Control-Return>',self.run);self.editor.bind('<Button-3>',self.edit_menu)
        foot=tk.Frame(right,bg=WHITE);foot.pack(fill='x',padx=u(13),pady=(u(11),u(9)))
        self.go=self.button(foot,'▶  运行',self.run,True);self.go.pack(side='left')
        self.halt=self.button(foot,'停止',self.stop);self.halt.pack(side='left',padx=u(7));self.halt.config(state='disabled')
        self.reset=self.button(foot,'恢复示例',self.restore);self.reset.pack(side='right')
        self.status=self.lbl(right,'',14,MUTE,WHITE,anchor='w',justify='left')
        self.status.pack(fill='x',padx=u(15),pady=(0,u(9)));right.bind('<Configure>',lambda e:self.status.config(wraplength=max(80,e.width-u(36))))

    def scroll_editor(self,a,b):
        self.vbar.set(a,b);self.root.after_idle(self.draw_gutter)

    def draw_gutter(self):
        self.gutter.delete('all')
        idx=self.editor.index('@0,0')
        while True:
            info=self.editor.dlineinfo(idx)
            if info is None:break
            num=int(idx.split('.')[0]);y=info[1]+info[3]/2
            self.gutter.create_text(self.u(23),y,text=str(num),anchor='e',font=self.font(13,False,True),fill=MUTE)
            idx=self.editor.index(f'{num+1}.0')
            if self.editor.compare(idx,'>=','end-1c'):break

    def syntax(self):
        self.after_syntax=None
        for tag in ('kw','num','str','comment','fn'):self.editor.tag_remove(tag,'1.0','end')
        src=self.source()
        try:
            for tok in tokenize.generate_tokens(io.StringIO(src).readline):
                tag={tokenize.NUMBER:'num',tokenize.STRING:'str',tokenize.COMMENT:'comment'}.get(tok.type)
                if tok.type==tokenize.NAME:
                    if tok.string in ('for','in','import','as','range','pass'):tag='kw'
                    elif tok.string in ('forward','backward','right','left','goto','penup','pendown','pencolor','color','pensize','shape','speed','done','setheading'):tag='fn'
                if tag:self.editor.tag_add(tag,'%d.%d'%tok.start,'%d.%d'%tok.end)
        except (IndentationError,tokenize.TokenError,SyntaxError):pass
        self.draw_gutter()

    def source(self):return self.editor.get('1.0','end-1c')
    def load_text(self,src):
        self.loading=True
        self.editor.delete('1.0','end');self.editor.insert('1.0',src)
        self.editor.edit_reset();self.editor.edit_modified(False)
        self.editor.mark_set('insert','1.0');self.editor.yview_moveto(0);self.editor.xview_moveto(0)
        self.loading=False;self.syntax()
    def modified(self,event=None):
        if self.loading or not self.editor.edit_modified():return
        self.editor.edit_modified(False);self.snippets[self.current]=self.source()
        self.cancel_play();self.editor.tag_remove('err','1.0','end')
        self.status.config(text='代码已修改，点“运行”试一试。',fg=MUTE)
        if self.after_syntax is not None:self.root.after_cancel(self.after_syntax)
        self.after_syntax=self.root.after(100,self.syntax)

    def indent(self,event=None):
        self.editor.insert('insert','    ');return 'break'
    def newline(self,event):
        if event.state & 4:return self.run()
        start=self.editor.get('insert linestart','insert')
        spaces=len(start)-len(start.lstrip(' '))
        self.editor.insert('insert','\n'+' '*(spaces+(4 if start.rstrip().endswith(':') else 0)))
        return 'break'
    def edit_menu(self,e):
        m=tk.Menu(self.root,tearoff=False,font=self.font(14))
        for label,cmd in [('撤销','Undo'),('剪切','Cut'),('复制','Copy'),('粘贴','Paste'),('全选','SelectAll')]:
            m.add_command(label=label,command=lambda c=cmd:self.editor.event_generate('<<'+c+'>>'))
        try:m.tk_popup(e.x_root,e.y_root)
        finally:m.grab_release()
    def switch(self,e=None):
        self.snippets[self.current]=self.source();self.current=self.choice.get()
        self.hint.config(text=SAMPLES[self.current][0]);self.show_sheep.set(self.visibility[self.current])
        self.load_text(self.snippets[self.current]);self.run()
    def restore(self):
        if self.source()!=SAMPLES[self.current][2] and not messagebox.askyesno('恢复示例','用示例代码替换右侧的内容？',parent=self.root):return
        self.snippets[self.current]=SAMPLES[self.current][2];self.load_text(self.snippets[self.current]);self.run()
    def toggle_sheep(self):
        self.visibility[self.current]=self.show_sheep.get();self.repaint()
    def save_file(self,event=None):
        path=filedialog.asksaveasfilename(parent=self.root,title='保存 Python 代码',defaultextension='.py',
            initialfile=self.current+'.py',filetypes=[('Python 代码','*.py'),('所有文件','*')])
        if path:
            try:Path(path).write_text(self.source(),encoding='utf-8');self.status.config(text='代码已保存。',fg=MUTE)
            except OSError as e:messagebox.showerror('保存失败',str(e),parent=self.root)
        return 'break'
    def open_file(self,event=None):
        path=filedialog.askopenfilename(parent=self.root,title='打开 Python 代码',filetypes=[('Python 代码','*.py'),('所有文件','*')])
        if not path:return 'break'
        try:
            with tokenize.open(path) as f:src=f.read(32001)
            if len(src)>32000:raise ValueError('文件超过 32000 个字符，请选一段课堂代码。')
        except (ValueError,OSError,SyntaxError,UnicodeError) as e:
            messagebox.showerror('打开失败',str(e),parent=self.root);return 'break'
        if self.snippets['自由画布']!=SAMPLES['自由画布'][2] and not messagebox.askyesno('打开代码','用这个文件替换自由画布里的代码？',parent=self.root):return 'break'
        self.snippets[self.current]=self.source();self.snippets['自由画布']=src
        self.current='自由画布';self.choice.set(self.current);self.hint.config(text=SAMPLES[self.current][0])
        self.show_sheep.set(False);self.visibility[self.current]=False;self.load_text(src);self.run()
        return 'break'

    def cancel_play(self):
        if self.pending is not None:self.root.after_cancel(self.pending);self.pending=None
        self.running=False;self.halt.config(state='disabled');self.last_line=0
        self.editor.tag_remove('here','1.0','end')
    def stop(self,event=None):
        if self.running:
            self.cancel_play();self.status.config(text='已停止。点“运行”可以从起点再画一次。',fg=MUTE)
        return 'break'
    def valid_color(self,c):
        try:self.root.winfo_rgb(c);return True
        except tk.TclError:return False
    def mark(self,line,tag):
        self.editor.tag_remove(tag,'1.0','end')
        self.editor.tag_add(tag,f'{line}.0',f'{line}.end+1c')
        self.editor.see(f'{line}.0')
    def run(self,event=None):
        self.cancel_play()
        self.editor.tag_remove('err','1.0','end')
        try:new=plan(self.source(),self.valid_color)
        except LessonError as e:
            self.mark(e.line,'err');self.status.config(text=f'第 {e.line} 行 · {e}',fg=ERROR)
            return 'break'
        self.actions=new;self.count=0;self.progress=0.;self.position=(0,0);self.heading=0.
        # Keep the same camera for the lesson's 100- and 150-step pens; expand for drawings outside it.
        x=[0];y=[0]
        for a in new:x.append(a.end[0]);y.append(a.end[1])
        self.view=(min(-70,min(x)-18),max(185,max(x)+18),min(-166,min(y)-18),max(52,max(y)+18))
        self.repaint()
        if not new:
            self.status.config(text='试试在代码框里加上 t.forward(100)。',fg=MUTE)
            return 'break'
        self.halt.config(state='normal');self.running=True;self.step_start=time.monotonic()
        self.tick();return 'break'

    def resize(self,event=None):
        if self.resize_id is not None:self.root.after_cancel(self.resize_id)
        self.resize_id=self.root.after(35,self.repaint)
    def transform(self):
        x0,x1,y0,y1=self.view;w=max(2,self.canvas.winfo_width());h=max(2,self.canvas.winfo_height());margin=self.u(20)
        self.scale=max(.001,min(max(1,w-margin*2)/(x1-x0),max(1,h-margin*2)/(y1-y0)))
        self.ox=w/2-(x0+x1)*self.scale/2;self.oy=h/2+(y0+y1)*self.scale/2
    def xy(self,x,y):return self.ox+x*self.scale,self.oy-y*self.scale
    def segment(self,a,end,tag):
        if a.draw and math.dist(a.start,end)>1e-8:
            self.canvas.create_line(*self.xy(*a.start),*self.xy(*end),fill=a.color,
                width=max(1,min(self.u(110),a.width*self.scale)),capstyle='round',tags=tag)
    def repaint(self):
        self.resize_id=None;self.transform();c=self.canvas;c.delete('all')
        w=c.winfo_width();h=c.winfo_height();gap=self.u(28)
        # A faint dot grid gives children a fixed reference when they change the distance.
        for x in range(gap//2,w,gap):
            for y in range(gap//2,h,gap):
                c.create_oval(x,y,x+1,y+1,outline='',fill='#E2E4D1',tags='grid')
        if self.show_sheep.get():c.create_image(*self.xy(50,-50),image=self.sheep,tags='sheep')
        for a in self.actions[:self.count]:self.segment(a,a.end,'trail')
        if self.count<len(self.actions) and self.progress>0:
            self.segment(self.actions[self.count],self.position,'live')
        self.redraw_turtle()
    def redraw_turtle(self):
        x,y=self.position;a=self.heading
        angle=int((a+5)//10*10)%360
        self.canvas.delete('sprite');self.canvas.create_image(*self.xy(x,y),image=self.turtles[angle],tags='sprite')
        self.coord.config(text=f'位置  ({round(x)}, {round(y)})')
        self.rtlabel.config(text=f'朝向  {round(a)%360}°')
    def tick(self):
        self.pending=None
        if not self.running:return
        start=time.monotonic()
        while self.count<len(self.actions):
            a=self.actions[self.count];now=time.monotonic()
            length=math.dist(a.start,a.end)
            duration=0 if a.speed==0 else min(2.4,max(.07,length/(85+24*a.speed),abs(a.turn)/(170+44*a.speed)))
            frac=1 if duration==0 else min(1,(now-self.step_start)/duration)
            self.progress=frac
            self.position=tuple(p+(q-p)*frac for p,q in zip(a.start,a.end))
            self.heading=(a.heading+a.turn*frac)%360
            if self.last_line!=a.line:
                self.last_line=a.line;self.mark(a.line,'here')
                self.status.config(text=f'第 {a.line} 行 · {a.label}',fg=GREEN)
            self.canvas.delete('live')
            if frac<1:
                self.segment(a,self.position,'live');break
            self.segment(a,a.end,'trail');self.count+=1;self.progress=0;self.step_start=now
            if now-start>.012:break
        self.redraw_turtle()
        if self.count==len(self.actions):
            self.cancel_play();num=sum(s.draw and math.dist(s.start,s.end)>1e-8 for s in self.actions)
            self.status.config(text=f'画完了，共画了 {num} 段线。',fg=GREEN)
        else:self.pending=self.root.after(16,self.tick)

    def help(self):
        if self.helpwindow is not None and self.helpwindow.winfo_exists():
            self.helpwindow.lift();return
        win=tk.Toplevel(self.root);self.helpwindow=win;win.title('指令手册');win.configure(bg=PAPER);win.transient(self.root)
        wrap=tk.Frame(win,bg=PAPER);wrap.pack(fill='both',expand=True,padx=self.u(22),pady=self.u(18))
        self.lbl(wrap,'小海龟听得懂的指令',23,INK,PAPER,True).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,self.u(9)))
        rows=[('t.forward(100)','朝前走 100 步'),('t.backward(30)','向后退 30 步'),('t.left(90)  /  t.right(90)','向左或向右转 90°'),('t.pencolor("red")','换颜色，如 red、blue、purple'),('t.pensize(5)','把线宽设为 5'),('t.penup()  /  t.pendown()','抬笔移动 / 落笔画线'),('t.goto(0, 0)','走到坐标 (0, 0)'),('t.setheading(0)','面向右方，90 表示上方'),('t.speed(0)','立即画完；1 到 10 逐渐加快'),('for i in range(4):','把下面缩进的指令重复 4 次')]
        for i,(a,b) in enumerate(rows,1):
            tk.Label(wrap,text=a,font=self.font(15,False,True),bg=PAPER,fg=GREEN).grid(row=i,column=0,sticky='w',pady=self.u(3))
            self.lbl(wrap,b,14,MUTE,PAPER).grid(row=i,column=1,sticky='w',padx=(self.u(14),0))
        self.lbl(wrap,'支持课堂用的 turtle 指令、变量、四则运算和嵌套 for 循环。',13,MUTE,PAPER).grid(row=len(rows)+1,column=0,columnspan=2,sticky='w',pady=(self.u(12),0))
        self.button(wrap,'回到画室',win.destroy).grid(row=len(rows)+2,column=1,sticky='e',pady=(self.u(10),0))
        win.bind('<Escape>',lambda e:win.destroy())
    def about(self):
        messagebox.showinfo('关于小海龟画室','小海龟画室 1.0\n\n小海龟、小羊来自配套课件中的 OpenMoji 插图。\nhttps://openmoji.org/\nCC BY-SA 4.0 · https://creativecommons.org/licenses/by-sa/4.0/\n海龟图像经翻转、旋转和缩放，小羊经缩放；改编图像沿用相同许可。\n\n程序内置 CPython 与 Tcl/Tk。',parent=self.root)
    def close(self):
        self.cancel_play();self.root.destroy()


if __name__=='__main__':
    root=tk.Tk();app=Studio(root);root.mainloop()
