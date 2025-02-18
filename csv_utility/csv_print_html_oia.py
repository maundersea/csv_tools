#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Name:         csv_print_html_oia.py
# Description:
#
# Author:       m.akei
# Copyright:    (c) 2021 by m.na.akei
# Time-stamp:   <2021-04-25 16:33:53>
# Licence:
# ----------------------------------------------------------------------
import argparse
import textwrap
import sys

from pathlib import Path

import re
import html

import minify_html
import json

import pandas as pd

VERSION = 1.0

OIA_HANDLER_JS = "oia_handler.js"


def init():
    arg_parser = argparse.ArgumentParser(description="print html table made of csv with estimation",
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         epilog=textwrap.dedent('''
remark:
  

  For '--part_color', is you want to use comma(,) an colon(:) in word, then those must be escaped by "\".


example:
  cat test3.csv
IDX,B,C,O,I,A
1,A,Sample1,Observation1:this is a pen,Investigation1:Atre you there?,Action1: nothing to do
2,B,Sample2,Observation2:this is a pen,Investigation2:Atre you there?,Action2: nothing to do
3,C,Sample3,Observation3:this is a pen,Investigation2:Atre you there?,Action3: nothing to do

  csv_print_html_oia.py --columns=IDX,B,C --part_color='this:red' test3.csv  O I A > test.html
  csv_print_html_oia.py --columns=IDX,B,C --part_color='バリ島:red,米国:green,潜水艦:blue,海軍:black' --search_on_html test3.csv  O I A > test.html

'''))

    arg_parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(VERSION))

    arg_parser.add_argument("--title", dest="TITLE", help="Title of table", type=str, metavar='TITLE', default=None)

    arg_parser.add_argument("--columns",
                            dest="COLUMNS",
                            help="names of addtional columns",
                            type=str,
                            metavar='COLUMNS[,COLUMNS...]',
                            default=None)

    arg_parser.add_argument("--part_color",
                            dest="PCOLORS",
                            help="part color for string, color code is one in css codes.",
                            type=str,
                            metavar='STRING:COLOR[,STRING:COLOR...]',
                            default=None)
    arg_parser.add_argument("--search_on_html", dest="SHTML", help="searching on html is enable", action="store_true", default=False)

    arg_parser.add_argument("--output_file", dest="OUTPUT", help="path of output file", type=str, metavar='FILE', default=sys.stdout)
    arg_parser.add_argument("--minify", dest="MINIFY", help="minifing html", action="store_true", default=False)

    arg_parser.add_argument('csv_file', metavar='CSV_FILE', help='file to read, if empty, stdin is used')

    arg_parser.add_argument('oia_columns', metavar='COLUMNS', nargs="+", help="colum names of Observation/Investigation/Action")

    args = arg_parser.parse_args()
    return args


def html_prologe_oia(align_center=True, width=None, word_colors="", search_on_html=False, progress_bar=False, title=""):
    table_css_2 = ""
    if align_center:
        table_css_2 += "margin-left: auto;margin-right: auto;"
    if width is not None:
        table_css_2 += "width:{};".format(width)
    # text-shadow: 0.1em 0.1em 0.6em gold;
    table_css = '''
    <style type="text/css">
      /* */
      body {{
        background: -webkit-linear-gradient(left, #25c481, #25b7c4);
        background: linear-gradient(to right, #25c481, #25b7c4);
      }}
      h2.title {{
        text-align:center;
        margin-bottom: 0pt;
      }}
      form.word_search {{
        position: fixed;
        top: 1.5em;
        visibility:hidden;
        z-index: 100;
      }}
      span.word_view_span {{
        font-weight:bold;
        background:#EEEEEE;
        box-shadow: 0.0625em 0.0625em 0.0625em 0.0625em rgba(0,0,0,0.4);
        border-radius: 0.25em;
        padding-left:0.2em;
        padding-right:0.2em;
	margin-right:0.2em;
      }}
      fieldset {{
        border: 2px solid #ccc;
        border-radius: 5px;
        padding: 25px;
        margin-top: 20px;
        background-color: #e0ffff;
        box-shadow: 5px 5px 5px rgba(0,0,0,0.2);
      }}
      legend {{
        border:  1px solid #ccc;
        border-bottom: 0;
        border-radius: 5px 5px 0 0;
        padding: 8px 18px 0;
        position:relative;
        top: -14px;
        background-color: #e0ffff;
      }}
      td.dblclicable:hover {{
         font-weight:bold;
         font-size:110%;
      }}

      table {{ 
         {}
         box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
      }}
      table caption {{
         font-size:large; font-weight: bold;
      }}
      th {{
          /* background-color: #6495ed; */
         background-color: #009879;
	 padding:6px;
      }}
      thead tr th {{
         border-bottom: solid 1px;
         color: #ffffff;
      }}
      td {{
         padding:6pt; 
      }}
      /* Table CSS: Creating beautiful HTML tables with CSS - DEV Community https://dev.to/dcodeyt/creating-beautiful-html-tables-with-css-428l */
      tbody tr {{
         border-bottom: 1px solid #dddddd;
         background-color: #ffffff;
      }}
      tbody tr:last-of-type {{
         border-bottom: 2px solid #009879;
      }}
      /*  CSSのposition: stickyでテーブルのヘッダー行・列を固定する - Qiita https://qiita.com/orangain/items/6268b6528ab33b27f8f2 */
      table.sticky_table thead th {{
         position: -webkit-sticky;
         position: sticky;
         top: 0;
         z-index: 1;
      }}
      table.sticky_table th:first-child {{
         position: -webkit-sticky;
         position: sticky;
         left: 0;
      }}
      table.sticky_table thead th:first-child {{
         z-index: 2;
      }}
    </style>
'''.format(table_css_2)

    text = """
<?xml version="1.0" encoding="utf-8"?>
<html>
  <!-- made by csv_print_html_oia.py -->
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Cache-Control" content="no-store">
    <meta http-equiv="Expires" content="0">
{}
  </head>
  <body>
""".format(table_css)
    if title is not None and len(title) > 0:
        text += f'<h2 class="title">{title}</h2>'

    word_colors = re.sub(r"\"", "&quot;", word_colors)
    if search_on_html:
        text += """
   <script type="text/javascript" src="{}"></script>
   <script type="text/javascript">
        // クリック時に特殊キーを検知させる http://www.shurey.com/js/samples/1_tips16.html
        KEY_SHIFT = false;
        KEY_CTL = false;
        KEY_ALT = false;
        KEY_META = false;
        document.onkeydown = function(event) {{
                var key_event = event|| window.event;
                KEY_SHIFT = (key_event.shiftKey);
                KEY_CTL = (key_event.ctrlKey);
                KEY_ATL = (key_event.altKey);
                KEY_META = (key_event.metaKey);
        }}
        document.onkeyup = function(event) {{
                var key_event = event|| window.event;
                KEY_SHIFT = (key_event.shiftKey);
                KEY_CTL = (key_event.ctrlKey);
                KEY_ATL = (key_event.altKey);
                KEY_META = (key_event.metaKey);
        }}

        function oia_dblclick_from_td_0(val_dic){{
            if(typeof(oia_dblclick_from_td) == "function"){{
                oia_dblclick_from_td(val_dic);
            }} else {{
                alert("リンク先が設定されていません");
            }}
        }}
   </script>
   <script type="text/javascript">
        window.onload=function(){{
            if( window.location.hash.length > 0){{
                window.scroll(0,window.scrollY-32);
            }}
            if( window.location.search.length > 0){{
                let search_string=decodeURI(window.location.search.substring(1));
                window.find(search_string,false,false,true,false,true);
            }}
            show_hide_progress_bar(false);
        }}
        function show_hide_progress_bar(onoff){{
            let prg_elm= document.getElementById("progfs");
            if( prg_elm){{
                if(onoff){{
                    prg_elm.style.visibility="visible";
                }} else {{
                    prg_elm.style.visibility="hidden";
                }}
            }}
        }}
        function show_nrec_record(nrec,onoff){{
            let tr_objs= document.evaluate("/html//tr[@nrec=\\""+nrec+"\\"]",document,null,XPathResult.ANY_TYPE, null);
            let tr_node= tr_objs.iterateNext();
            while(tr_node){{
                if( onoff ){{
                    tr_node.style.display="";
                }} else {{
                    tr_node.style.display="none";
                }}
                tr_node= tr_objs.iterateNext();
            }}
        }}
        function show_nohits_record(obj){{
            if( obj.checked){{
                onoff=true;
            }} else {{
                onoff=false;
            }}
            let xp_results_0= document.evaluate("/html//td[@hits_status=\\"1\\"]",document,null,XPathResult.ANY_TYPE, null);
            let node= xp_results_0.iterateNext();
            let nrec_hits=[];
            while( node){{
                let nrec= node.getAttribute("nrec");
                nrec_hits.push(nrec);
                show_nrec_record(nrec,true);
                node= xp_results_0.iterateNext();
            }}
            show_nrec_record(onoff);
            let xp_results= document.evaluate("/html//td[@hits_status=\\"0\\"]",document,null,XPathResult.ANY_TYPE, null);
            node= xp_results.iterateNext();
            while( node){{
                let nrec= node.getAttribute("nrec");
                if( nrec_hits.indexOf(nrec) != -1){{
                    node= xp_results.iterateNext();
                    continue;
                }}
                show_nrec_record(nrec, onoff);
                node= xp_results.iterateNext();
            }}
        }}
        function word_color(word,color_code){{
            var nodes= document.getElementsByTagName("td");
            let count=0;
            for(var i=0; i< nodes.length; i++){{
                // let wre= word.replace(/[\\^$.*+?()\\[\\]{{}}|]/g, '\\\\$&');
                let wre= word.replace(/</g, '&lt;');
                wre= wre.replace(/>/g, '&gt;');
                let re= new RegExp('(?<!<[^>]*)('+wre+')','gi');
                nodes[i].innerHTML=nodes[i].innerHTML.replace(re,'<span class="word_view_span" style="color:'+color_code+'">$1</span>');
                count_0= (nodes[i].innerHTML.match(re) ||[]).length;
                if( count_0 > 0){{
                    nodes[i].setAttribute("hits_status","1");
                }} else if(nodes[i].getAttribute("hits_status") == 0){{
                    nodes[i].setAttribute("hits_status","0");
                }}
                count= count+ count_0;
            }}
            return count;
        }}
        function word_color_reset(){{
            var nodes= document.getElementsByTagName("td");
            for(var i=0; i< nodes.length; i++){{
                span_head='<span class="word_view_span"'
                let re = new RegExp(span_head+' style="color:[^\"]+">([^<]+?)</span>','gi');
                while( nodes[i].innerHTML.indexOf(span_head) != -1){{
                    nodes[i].innerHTML=nodes[i].innerHTML.replace(re,'$1');
                    nodes[i].setAttribute("hits_status","0");
                }}
            }}
        }}
        function emphasis_words(obj){{
            let wc_defs= obj.value;
            let re_s= new RegExp(/(?<!\\\\)\s*,\s*/,'g')
            obj.value= obj.value.replace(re_s,", ");
            let re= /\s*(?<!\\\\),\s*/;
            let cvs= wc_defs.split(re);
            let word_counts={{}};
            word_color_reset();
            show_hide_progress_bar(true);
            cvs.forEach(
                function (val ){{
                    if(val==""){{
                        return;
                    }}
                    let re= /\s*(?<!\\\\):\s*/;
                    cvs=val.split(re);
                    var w="";
                    var c="";
                    if( cvs.length < 2){{
                        // alert("??error:word_view:invalid definition: '"+val+"'");
                        w= cvs[0];
                        c="red";
                    }} else {{
                        let re= new RegExp('\\\\\\\\([,:])','g');
                        w= cvs[0];
                        w=w.replace(re,'$1');
                        c= cvs[1];
                    }}
                    if(!c.match(/^[a-zA-Z0-9#]+$/)){{
                        alert("??error:word_view:invalid color code: '"+c+"'");
                        return;
                    }}
                    try{{
                        word_counts[String(w)]=word_color(w,c);
                    }} catch(e){{
                        alert("??error:word_view:invalid definition: '"+val+"' :"+e);
                    }}
                }}
            );
            let sh_obj= document.getElementById("showhide_hits");
            show_nohits_record(sh_obj);
            let swr= document.getElementById('search_word_result');
            swr.innerHTML="検索結果:"+JSON.stringify(word_counts);
            show_hide_progress_bar(false);
        }}
        function show_word_search(){{
            let fobj= document.getElementById("word_search");

            sty_visibility=fobj.style.visibility;
            if( sty_visibility == "" || sty_visibility == "hidden"){{
                fobj.style.visibility="visible";
            }} else {{
                fobj.style.visibility="hidden";
            }}
        }}
   </script>
    <form action="" onsubmit="return false;" class="word_search" id="word_search" ondblclick="show_word_search();">
      <fieldset style="padding-top:0pt;padding-bottom:0pt;">
	<legend>語句色付け定義</legend>
	<input type="text" size="138" placeholder="Enter word:color[,word:color...]" onchange="emphasis_words(this)" value="{}"><br/>
	<input type="checkbox" id="showhide_hits" name="showhide_hits" checked onchange="show_nohits_record(this)"/>
        <label for="showhide_hist" style="font-size:0.5em;">全レコード表示</label><br/>
        <span style="font-size:0.5em;">
	語句の色付け定義を"語句:色"で入力。複数入力する場合は半角カンマで区切って入力、語句には正規表現を利用可能<br>
        語句だけ指定した場合は、赤色が指定されたものとして処理される。
        語句に半角カンマ、コロンを含める場合はBackslash(\\)によりエスケープする必要がある。
        また、&lt;&gt;は検索時に&amp;lt;&amp;gt;として検索されることに注意。<br>
        Ex: ABC:red,DEF\,GHI:blue,\d+人:black
        </span><br>
        <span style="font-size:small;" id="search_word_result"></span>
      </fieldset>
    </form>
""".format(OIA_HANDLER_JS, word_colors)
    else:
        text += f'<input value="{word_colors}" style="display:none" />\n'

    if progress_bar:
        text += """
      <fieldset id="progfs" 
                style="padding-top:0pt;padding-bottom:0pt;position:fixed;height:2em;top:1em;right:10;background-color:white;z-index:100;padding:0.5em;background-color: #e0ffff;">
	<label for="progbar" style="font-size:0.5em;">しばらくお待ちください</label>
	<progress id="progbar" style="width:20em;height:1em;"></progress>
      </fieldset>
"""

    return text


def html_epiloge(datatable=False):
    # DataTables example - Scroll - horizontal and vertical https://datatables.net/examples/basic_init/scroll_xy.html
    if datatable:
        text = '''
<script type="text/javascript">$(document).ready(function(){$('table').DataTable({
    lengthChange: false,
    scrollX: true,
    scrollY: "80vh",
    paging: false
});});</script>
'''
    else:
        text = ""

    text += '''
  </body>
</html>
'''
    return text


def part_color(pcolors, text):
    hit_words = {}
    for pc in pcolors:
        cvs = re.split(r"(?<!\\):", pc)
        if len(cvs) < 2:
            # print(f"??error:csv_print_html:invalid format for --part_color:{pc}", file=sys.stderr)
            # sys.exit(1)
            cvs.append("red")
        w = cvs[0]
        w = re.sub(r"\\([,:])", r"\1", w)
        w = w.strip("'\"")
        w_0 = w
        w = html.escape(str(w))
        w0 = "(" + w + ")"
        c = cvs[1]
        fmt = f"color:{c};"
        sp = f'<span class="word_view_span" style="{fmt}">\\1</span>'
        text_0 = text
        text = re.sub(w0, sp, text)
        if text_0 != text:
            hit_words[w_0] = text_0.count(w_0)
    return text, hit_words


def make_table(df, columns, oia_columns, pcolors, space_width="40pm"):
    output_df = df.copy()
    output_df["hits_words"] = ""
    html_str = '\n<table class="sticky_table display nowrap" style="width:100%;">\n'
    html_str += '<thead ondblclick="show_word_search();">\n'
    n_oia = len(oia_columns)
    for c in columns:
        html_str += f"<th>{c}</th>\n"
    html_str += f'<th colspan="{n_oia+1}">Observation/Investigation/Action</th>\n'
    html_str += '</thead>\n<tbody>\n'

    df.fillna("", inplace=True)
    for ir, row in df.iterrows():
        if ir % 2 == 0:
            tr_sty = 'style="background-color:#eeffee;"'
        else:
            tr_sty = ""
        html_str += f"<tr {tr_sty} nrec=\"{ir}\" id=\"rid_{ir}\">\n"
        check_empty = all([v == "" for v in row[oia_columns]])
        n_oia_h = 1 if check_empty else n_oia
        td_columns = {"nrec": ir}
        html_str_0 = ""
        for c in columns:
            v = html.escape(str(row[c]))
            td_columns[c] = v
            if pcolors is not None and len(pcolors) > 0:
                v, hw = part_color(pcolors, v)
            v = "&nbsp;" if v == "" else v
            html_str_0 += f"<td nowrap=1 rowspan='{n_oia_h}' ondblclick='oia_dblclick_from_td_0()' class='dblclicable'>{v}</td>\n"
        html_str_0 = re.sub(r"oia_dblclick_from_td_0\(\)", f"oia_dblclick_from_td_0({json.dumps(td_columns, ensure_ascii=False)})",
                            html_str_0)
        html_str += html_str_0
        if not check_empty:
            hits_words = {}
            for ic, c in enumerate(oia_columns):
                v = html.escape(str(row[c]))
                if pcolors is not None and len(pcolors) > 0:
                    v, hw = part_color(pcolors, v)
                    hits_words.update(hw)
                v = "&nbsp;" if v == "" else v
                hits_status = 1 if len(hits_words) > 0 else 0
                html_str += (f'<td width="{space_width}"></td>' *
                             ic) + f'<td colspan="{4-ic}" nrec="{ir}" hits_status="{hits_status}">{v}</td>\n'
                if ic < len(oia_columns) - 1:
                    html_str += f'</tr>\n<tr {tr_sty} nrec={ir}>\n'
            output_df.at[ir, "hits_words"] = output_df.at[ir, "hits_words"] + str(hits_words)
        else:
            html_str += '<td></td>' * n_oia
        html_str += "</tr>\n"
    html_str += "</tbody>\n</table>\n"

    return html_str, output_df


def make_oia_handler_template(columns, output_js):
    if Path(output_js).exists():
        print(f"#warn:csv_print_html_oia: {output_js} already exists.", file=sys.stderr)
        return
    js_str = f"""
// -*- coding:utf-8 mode:javascript -*-
// File: oia_handler.js

function oia_dblclick_from_td(val_dic){{
   // index: 'nrec' and {columns}    
   // special key(boolean):
   //     KEY_SHIFT, KEY_CTL, KEY_ALT, KEY_META
   // enter codes
   console.log(val_dic, KEY_SHIFT);
   alert("{output_js}を編集してください。");
   // let html_url="test.html";
   // let nrec= val_dic["nrec"]; // record number in csv
   // let id_in_html="rid_"+nrec;
   // let url=html_url+"#"+id_in_html;
   // window.open(url,"__blank");
}}
"""
    with open(output_js, "w") as f:
        print(js_str, file=f)

    print(f"%inf:csv_print_html_oia: {output_js} was created.", file=sys.stderr)


if __name__ == "__main__":
    output_js = OIA_HANDLER_JS

    args = init()
    csv_file = args.csv_file
    output_file = args.OUTPUT
    oia_columns = args.oia_columns

    title = args.TITLE
    columns_s = args.COLUMNS

    pcolors_s = args.PCOLORS

    search_on_html = args.SHTML

    html_minify = args.MINIFY

    pcolors = None
    if pcolors_s is not None:
        pcolors = re.split(r"\s*(?<!\\),\s*", pcolors_s)
        print(f"%inf:csv_print_html:part colors: {pcolors}", file=sys.stderr)
    else:
        pcolors_s = ""

    columns = []
    if columns_s is not None:
        columns = re.split(r"\s*,\s*", columns_s)

    if csv_file == "-":
        csv_file = sys.stdin
        output_csv_file = "output_oia.csv"
    else:
        output_csv_file = Path(csv_file).stem + "_output.csv"

    if output_file != sys.stdout:
        output_file = open(output_file, "w")

    csv_df = pd.read_csv(csv_file, dtype='object')

    progress_bar = len(csv_df) > 500
    html_str = html_prologe_oia(width=None, word_colors=pcolors_s, search_on_html=search_on_html, title=title, progress_bar=progress_bar)
    html_str += "<div id='tablecontainer'>"
    table_str, output_df = make_table(csv_df, columns, oia_columns, pcolors)
    html_str += table_str
    html_str += "</div>"
    html_str += html_epiloge()

    if html_minify:
        try:
            html_str = minify_html.minify(html_str, minify_js=True, minify_css=True)
        except SyntaxError as e:
            mes = f'??error:csv_print_html_oia:{e}'
            print(mes, file=sys.stderr)
            sys.exit(1)

    print(html_str, file=output_file)
    if pcolors is not None:
        output_df.to_csv(output_csv_file, index=False)
        print(f"%inf:csv_print_html: {output_csv_file} was created.", file=sys.stderr)

    make_oia_handler_template(columns, output_js)
