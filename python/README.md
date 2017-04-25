# Brocade VDX 用 python スクリプト
[Brocade VDX ](http://www.brocade.com/ja/products-services/switches/data-center-switches/vdx-6740-switches.html)の NOS7.0 では、スイッチの中で Python スクリプトを動かすことができ、オペレーションのスクリプト化が可能になっています。ここでは、KLab で作ったも VDX 用 Python スクリプトの中から一般的に使えそうなものを公開します。

## diff.py
UNIX OS 上における diff コマンドのように、2つのテキストの内容を比較して異なっている部分を出力するスクリプトです。スイッチ上にあるファイル同士や、VDX の CLI コマンドの実行結果同士を比較することができます。

### 使用例
#### コマンドの実行結果同士の比較
* コマンドを指定する際は、 `"` でくくります。

```
sw01# python diff.py "show interface tengigabitethernet 19/0/1" "show interface tengigabitethernet 19/0/2"
--- show interface tengigabitethernet 19/0/1

+++ show interface tengigabitethernet 19/0/2

@@ -1,8 +1,8 @@

-TenGigabitEthernet 19/0/1 is up, line protocol is down (link protocol down)
-Hardware is Ethernet, address is c4f5.7cXX.XXX3
-    Current address is c4f5.7cXX.XXX3
+TenGigabitEthernet 19/0/2 is up, line protocol is down (link protocol down)
+Hardware is Ethernet, address is c4f5.7cXX.XXX4
+    Current address is c4f5.7cXX.XXX4
 Fixed Copper RJ45 Media Present
-Interface index (ifindex) is 81805713408
+Interface index (ifindex) is 81805721600
 MTU 2500 bytes
 LineSpeed Actual     : Nil
 LineSpeed Configured : Auto, Duplex: Full
```

#### ファイル同士の比較
* ファイルを指定する際は、ファイル名の頭に `f:` をつけて下さい。
* `-l` オプションで、表示する前後行数を指定できます。

```
sw01# # python diff.py -l1 f:defaultconfig.novcs f:defaultconfig.vcs                                        --- f:defaultconfig.novcs
--- f:defaultconfig.novcs

+++ f:defaultconfig.vcs

@@ -1,5 +1,2 @@

-!
-no protocol spanning-tree
-!
-vlan dot1q tag native     
+vlan dot1q tag native
 !
@@ -9,3 +6,3 @@

 priority-group-table 15.0 pfc off
-priority-group-table 1 weight 40 pfc on
+priority-group-table 1 weight 40 pfc on
 priority-group-table 2 weight 60 pfc off
@@ -14,3 +11,3 @@

 interface Vlan 1
-shutdown
+no shutdown
 !
@@ -24,2 +21,15 @@

 !
+fcoe
+ fabric-map default
+  vlan           1002
+  priority       3
+  virtual-fabric 128
+  fcmap          0E:FC:00
+  advertisement interval 8000
+  keep-alive timeout
+ !                               
+ map default
+  fabric-map default
+  cee-map    default
+ !
 logging auditlog class CONFIGURATION
@@ -29,2 +39 @@

 end
-!
```

### オプション
```
usage: diff.py [-h] [-u | -c | -n] [-l N] left right

2つのファイルの内容もしくはコマンドの実行結果の差異を出力します。

positional arguments:
  left        1つめの diff のソースデータを指定します。 指定されたものが "f:"
              で始まっていた場合、それ以後の部分をファイル名としてみなし、指定されたファイルからデータを読み込みます。それ以外の場合は、VDX の CLI コマンドとして扱い、コマンドを実行した際の出力結果を使います。
              クォートする場合は `"` (ダブルクォート) を使って下さい。
  right       2つめの diff のソースデータを指定します。 leftと同様に指定します。

optional arguments:
  -h, --help  ヘルプを出力します。
  -u          unified diff 形式で出力します。 デフォルト
  -c          context diff 形式で出力します
  -n          differ diff 形式で出力します
  -l N        表示する前後の行数を指定します。 デフォルト値は 3 です。
              `-u' か `-c' オプションとのみ組み合わせられます。
```

## sample__port_parse_and_compose.py
VDX の CLI において、コマンドに対してポート番号を指定するには `RBridgeID/シャーシ番号/ポート番号` の形式でを使います。コマンドによってはポート番号は `,` や `-` を使って複数指定できます。しかし複数ポートの指定をできないコマンドも依然ありますし、 RBridgeID はロジカルシャーシ機能を使っている場合でも、複数指定することはできません。

決まったパターンのコマンドを複数の(スイッチの)ポートに対して実行したい場合、個々のポートごとにコマンドを発行するのは手間がかかるだけではなく、オペミスの可能性も増えます。そんな場面ではコマンドのスクリプト化が威力を発揮します。
そのようなスクリプトにおいて、操作対象のポートをコマンドライン引数で指定する場合に便利なコードサンプルがこちらです。中身は `argparse` を使った引数解析器とサポート関数で構成されています。

### 使用例
\# VCS 上に参加するスイッチの RBridgeID が `"11", "12", "13", "21", "22", "23"` の時

* RBridgeID とポート番号は、それぞれ `--rids` と `--ports` で指定します。
```
sw01# python3 sample__port_parse_and_compose.py --rids 11 --ports 1
['11/0/1']
```
* 複数ポートを指定する場合は、 `,` や `-` で指定します。 `--ports` を複数回使うこともできます。
```
sw01# python3 sample__port_parse_and_compose.py --rids 11 --ports 1,2
['11/0/1-2']
sw01# python3 sample__port_parse_and_compose.py --rids 11 --ports 1 --ports 2
['11/0/1-2']
sw01# python3 sample__port_parse_and_compose.py --rids 11 --ports 1 --ports 2-5
['11/0/1-5']
```
* RBridgeID もポートと同様に複数指定ができます
```
sw01# python3 sample__port_parse_and_compose.py --rids 11,21 --ports 1
['11/0/1', '21/0/1']
sw01# python3 sample__port_parse_and_compose.py --rids 11-13 --ports 1
['11/0/1', '12/0/1', '13/0/1']
```
* `--rids-pattern` を使うと、RBridgeID の指定に シェルスタイルのパターン指定ができます。パターンを適用する対象は VCS に参加しているスイッチの RBridgeID のリストです。
```
sw01# python3 sample__port_parse_and_compose.py --rids-pattern 1? --ports 1
['11/0/1', '12/0/1', '13/0/1']
sw01# python3 sample__port_parse_and_compose.py --rids-pattern 1[12] --ports 1
['11/0/1', '12/0/1']
sw01# python3 sample__port_parse_and_compose.py --rids-pattern ?[12] --ports 1
['11/0/1', '12/0/1', '21/0/1', '22/0/1']
```
* 通常の `RBridgeID/シャーシ番号/ポート番号` での指定もできます。
```
sw01# python3 sample__port_parse_and_compose.py --rids 11 --ports 1,2 23/0/1
['11/0/1-2', '23/0/1']
```

## doit.py
コマンドラインで指定された CLI コマンドを、指定されたポートに対して実行する。

### 実行例
* 第１引数に実行したいコマンドを指定します。コマンド中のポート番号の部分は `%s` に置き換えておきます。

```
h05u# python doit.py "show interface tengigabitethernet  %s | include Discards" 19,29/0/1 19/0/1-2
Namespace(command='show interface tengigabitethernet  %s | include Discards', fq_ports=['19,29/0/1', '19/0/1-2'], ports=None, rbridgeids=None, rids_pattern=None)
['19/0/1', '19/0/2', '29/0/1']
!Command: show interface tengigabitethernet  19/0/1 | include Discards
!Time: Tue Apr 25 20:49:21 2017

    Errors: 0, Discards: 0
    Errors: 0, Discards: 0

!Command: show interface tengigabitethernet  19/0/2 | include Discards
!Time: Tue Apr 25 20:49:21 2017

    Errors: 0, Discards: 0
    Errors: 0, Discards: 0

!Command: show interface tengigabitethernet  29/0/1 | include Discards
!Time: Tue Apr 25 20:49:22 2017

    Errors: 0, Discards: 0
    Errors: 0, Discards: 0

```
