import base64
import zlib
import time
import numpy as np
import pyvisa

# ============================================================
# KROWA 3D -> SIGLENT SDG6052X -> HAMEG HM303-6 (XY)
# ============================================================
# Model krowy jest ZASZYTY w tym pliku. Nie potrzeba cow.obj.
# CH1 generatora = X, CH2 generatora = Y.
#
# W trybie TrueArb używamy INTER,LINE, więc generator liniowo
# łączy kolejne wierzchołki siatki. Dzięki temu nie trzeba
# wstawiać tysięcy punktów na każdy odcinek.
# ============================================================

VISA_RESOURCE = "TCPIP0::192.168.98.52::inst0::INSTR"     # np. "USB0::0xF4EC::0x1102::...::INSTR"

VPP = 4.0
OFFSET = 0.0

# Animacja podobna do filmu: obrót modelu wokół osi pionowej.
ROTATION_PERIOD = 6.0    # sekundy / pełen obrót
ANIMATION_FPS = 20       # liczba różnych ustawień modelu na sekundę
TRACE_REPEATS = 3        # każda klatka rysowana 3x -> ok. 60 odświeżeń/s
ROTATION_DIRECTION = 1   # 1 albo -1

# Ustawienia obrazu
SCREEN_FILL = 0.86
CAMERA_DISTANCE = 4.0    # większe = słabsza perspektywa
TILT_X_DEG = -5.0        # lekkie pochylenie góra/dół
TILT_Z_DEG = 0.0

# Jeżeli obraz na Hamegu jest odbity, zmień odpowiednią opcję.
FLIP_X = False
FLIP_Y = False

# ============================================================
# ZASZYTY MODEL 3D
# 2903 wierzchołki, 5804 trójkąty źródłowej siatki.
# Ścieżka jest ciągłym obiegiem po krawędziach siatki.
# ============================================================

VERTEX_COUNT = 2903
PATH_COUNT = 17413

_VERTICES_B85 = (
    'c-mZic{o;I)V3)@B@~h<bD>Ep$+Oo+WFCtQi9{nRA!#B~5-ANDG$|!N&6GTQZOtkTDk@EyOEiy4eO~V$-@aado$FlNdG^_Rt##JA'
    '_kFLH(hczbMG0fdgYl5vE>O{4!A^ZJ!PfUXq1(h;?D`XZ{L-Zq5@ugvp)wk%IrAWR?P+6nd0jDaM<pEnR?V)aH?jv6m9TWYJXVI*'
    'voG4UaOqPu8yT~O{qQ*p31zYv(te6f*1QU>adPN*sgQYIy9g3{1DyJ%l+nB!kT}5{n{Ah~$G2+W%?E-RcG*m0RSlFLb3~c{`8$E|'
    'pTPwD(Jz;|`7$uC3Fy4PG2%Z^(wg3Rot0PylV?X_b=qd)^=t=t&4|R=p9+ZX^xd#ytUo@ueungZvKDUe2$btxLfRMRLGn>=yd8Rz'
    'EQntS_SO;jsQo@Uw{;l|f9;Ol=E;Eeg&7c=Jq5Rhek3wgiy*^n626=>5Uxy*gOjsTk;=+I<BSy8e}5@H;)Y;i9}TB=Z^ci|@-QfP'
    'Aw<gTz?!rD!KN$%bXFh0qB}}3=6V9$mi&juwEM&S{n4PCeIB(AsDa_PX`npgBC0nT!K(T=Nd5O1uOBf4ZI>BvqwO(%Ixq~3oEO0@'
    '&5szg#uTOwO@N@R4>)(WEhHMHL#D?cY?B!P-G8Nm#P=^6mD|E}pB#`I-GxW{4uP4at3bnCflvBEL9aF&v`UpZ&KL`R1(`4*PMMdh'
    'jE4(8c|gN^@Qd1EuyN}O_^qbFw_3-+>koP0kgvntt>eMJJptxE(&6D_V_^IAY}jF?%V+Jj0mX&OpaOKcc7rv%nVtdJ={o#Ck_v2J'
    'H5dNc_U6CdE5iMa%i+mXHU8y{0{AS6g1b+9a?4B=0Gmj#9^ReH+bF@UOkYTuqrpSzV7NWP2gc}j=axn0klpSJk-Jp*m-cb+Q`-Xq'
    'Z4~&?U!%bGbTG{Lp~(LW_kz?-;~{6CEdLSi00a6?f~L1JT<wn|Y*ciIX(PU)%ujnz1b-MO^A-Or8w+<V$HL0RFK}6=EreY0h69dI'
    'af6W+%*>WRb5RWzX^wyi|6Jk3wi?{0IvP%fdcwX3C$aD|fy;pbaNYb8#xJmeyggyycJ2fgjwIkYD-tSJUBs}2p%Bq87E~`ELKBmr'
    'khwnyqT8C#D{lx?ADaxH-+sgazGL9GRSeY6`G>zX2~6%k3udfP;Py?va64lPEIZwePfiJhoHYTk>1_`l+T;x@m8U{>kPhG9G8}A&'
    'MZn8>TKsE$Fa&$YzyRxBTy@!W7-WzH)n;A!{%679aCteD)+_L)O@1J|I2Y!7-e>)Wn<IN(2$~HFc;8bCrTemARhbfw7+{F%(ydUW'
    'p@}Cf)G>YOO0XEx8#PY%L3xMG&@p4|Z=!&|!ZTp(ts(d$QWeKEuZIfFvG_FoF%x_T1^;4#e=)%aSxQs{{0<E3^xyGQSHU>>sh!uE'
    '<89&J^(i>MXA3FHG=fi_p`G^)vkXE1K_nW__)5CP947r&2BOofgTy&i0h+ABvE;f6Jc~F;PP@C}V7q6e?czO>VQY;$YBb@eei4y<'
    'GX&jxcLBpQWhCr{4thozLguHJl30U*IHs-#XvBV&9ABk_Zhwuye%Khc&>HaUUoEiAvuElCgK%QtDEPa^1Sd_8!0-;6bO<-YA7SIL'
    '*e(Dx*QKKR<7qfFV+5pzEyF`5K6vy`6xgpV!S{y2s5^cbOkYxhPm`T6-y#~=wlmnC?t*=G4+dZT2GpCRhqFisY}LPoW3CKCqn}n_'
    '@~#nkDGfyZ(4nB_{sPywgy2~xb@*-l27e6)>>XnQYW452@KzAM%hiSUIiK)yAjO&#3)nuj4YlvN<GF{XFyFfk+q-nkd$Kjm8Q7I~'
    'nQw`5%SXfXVihj2kj4M<2weTC$^!zFFl8D*LzN0wdVGo*bl9Y=VQ+q3z6-`JmB6YC+T6nE6)Sk)2_8?4c~W|By!kK+ZqL-_$0TRj'
    'xzS;;%vzrhTd;}c{Y!)+d$qW&oHKLTpA1fqb$Ny63cEXXnK08sgQM3tN&KfQSRAXzXRJyiK{r=HiE}spdHQkEEp9bTo~X}zoV-GM'
    '%+CbZHQjjdigptEdN~a9@6X+pHGuR<gUp9&+@-+)G<Gh8^gV`r)!wo2g)f9Z2Q>MSAP4AmJ02P$jQIOYfe`X58H!G7bFafO5YQ_I'
    'Zkd_z2aOA1#+pRX->%IyZ1OvNG#b+XGv^+>7+TH-gX_?q{LJ^maHj7BP;j>7Hrp?N>_toXyh@#0np^?vclz*qpe3I=t^qQPTS;a^'
    '51#(I0V<x9kYjlkT%-LF{Q16>RLQDx)AU9ty=hIhxLR<v#m`{r4oi}$WzJh_U&4OoFX>Zh$7{Q_z^_09iN^Oa{I~rF_#c}uYIovG'
    'tv_{MPp@_26Zd?8*@3arou<Bg_Jns(Ga_7C)8@^kTVF#DzcbQFD}s4x?mY<8Dwn?d706!=Yyj*2b<*KAllh(_RbbJ6R_b9siT6*e'
    'f>W;#NUh{1bIsaZP&l|<8Yh{=SDLQ{clnW0o7xaQW4Im6du%3EvJT;U7TCeW8SW=%t`6oAPg}`{iDPVpF_M7ZA^bvQE17m$N76fP'
    '65pCQ2KvS3Nsep|<-Ju}NZrs3N%?`v{PuiXIDWcVlDjvIkF;tg3$_$UMm~?=-Qq_>X+)kR@Mt)X34TKcnPf<AXGHRe<u>r-xS1r`'
    'Y6|Zz^O|(a*OC0EKb8B<wdq_F4V=QW(_WGPxqdKg3eV{nv-X*eRKag5pBU&wtctc*scnwrVL!%_<Ep_@d*5k%!|v_UJzt(nk8F?N'
    '@4q^dP}7}Kt+Ubm=(T@Rm2dx~hd)o{nx2c;h5fqBtlu;qQuK#Ct&3#yGsC#Pauhr5(=7c7;rzVsM^;uOVL`<K{3@kbR8=Gm51hh>'
    '{?x;DyT`LJ+d_Ebz(~Az;e>RQbP7)&n1Q$c9Fz9B5XI+iOhrrOFuMueXL9WWsrXq%gSDB=;@2mI;kLGk>}O>xx11Y`Q-6<P%WY=y'
    '58MV-RU=s3?m66N`cUka>&G6goypbKUSq#whO(QI7=Ea>l>J(zz-&Iu;OpmCNHuSasCwD)?&mt*J#qP5JI5p8JRsx^SzwnTUG_GN'
    'x8ysJIlGTay^6xP&+yK@knSB7%Jr@7iIU<@>9$RwyieB_(yEgo9YBJ)mK7xnb_GexwL|#0sjcMMEFI~*j38cq3rG*|?Nz@z#w_U='
    'qta`ho$BaN{;uOWd)6CD4BmzD(;FPflO5wk+mP19M(|~xx$yqM3F+@?Q+WTDDtL77fYdfJlz;bWgtc0JQki^TKKE!#=UxjoFA;n}'
    'BG|v=p|cZr4|xYUIoBlVkzTwx{Tb|{Pb9NiC4BvYXHdP&g8V(|&i^iZ2<J35k{dT9++MZ`!eesDs0F}RBsIdhibrIFAK?$vu7PHK'
    'A2^pahX3b%8gSES=yhTwpEhbUcwd?XPd5zXdUO_y)sBT84~Fo8U##F!&$%Gjxisv4B>z~O17X{@OS||_<@<U|q3Wxn^sM?M9{shk'
    '^Sy-kl?eVT5&Ty&DQ*InId>ZrP0J-iuXykmF^}MM<Qa+GI)9!hdkcPh`bh@tbmvEo-3O(4;Sy^(e=b{5*ZKTRD|h~Q!aYdNUUgC!'
    'BNd(_6`ms%eoOj;gzz<PRbV`DtW;P}>5K?ZeqzbJ&gTnjE)~|92{BD7#62d&J*f~I+3J7YxGH%BmA&puBdxw-KvV-*jC5puhJV8R'
    '*^QvR4W){*^|-dn9k~78k4;g$h1b&W!M7f_qyv)9WAlbv@OgO<JMMB0FS^}@wAppikEcqoZSf6Qe?OX4oh!oO?{7h!&wJ^F3(N8N'
    '`>XK0bpqS`YdNmzR|jcr8cc4jCtk|B0&O~e?9=YC_&4|_)TXye7y8_0cNbiOve-y=w(K5jHn<7rE&fO^-TP1#=2-*YKPNFyRFLKz'
    'tM6PB<x5?GB-BA(dL&z3pa`SP8lY|N5Ee7m9X{FJg^Kar*vlg>5as^AHn83~8AdwX@4Obqkb_&6z~fnWVBZrnl91^N4t;OKus9FW'
    'l#~W5H{5`CmZ>B`(+f&VFGEAn4zgqWYVhb<1=GJ>AvfYCK%z}0Bz^fo`f08QoBR7Ash1oKxG^1q?`#35e*-~Zbu0YK$_Ilhn$XQ<'
    'Hq47i2BUHpFdVoOzE7D0;}%&%-sS{2Tt~oiW&{){?1jtk2xQLkfZlSc@OiB&`2I?QM|lUJtEm!P`x^$AG)iEz=MFMqK{Q+}Jqi1#'
    'pCW4CT%kSZIBYpRf+%;Tkp7#)S5ifqFPX#eXHqy~N5~s_J-G6z8n%y)CnxWB2dyF1;48aM;_D#`GH)-#k!wa|>E35#bmVpD^36i}'
    'vb>f=SKI@*UuY+h93b~R>cFX7kKO58LQ))_z)n*|ran5AbT}adZX3_;PRb<3n_j@w&(17*jSrDq`51~d)7Wb-FS2;oOL(v0%l>Em'
    'PbN2ky-!x>wJ?Sav$_jD0kxg?(~TNnLEr^e6%@{PhTH~+RHe=wwU7F3m}w@DH_s<9VGI%O6QM>XLS0ORdYK3{GRfX_0`kY{p|x@?'
    'Ia5>(RRzOP|5iCkeozJmH-=){(>gLkwi5IboN!)d6*+ukFR<ehe0cgcdA#Bv(B*!plf{ToM-!peCh|{iKsFoHIe(!ZC)*D((9PJw'
    'wl~})LcLG+W>mm6yENAO?k^(X12E&!f3WvbB-60y1p=M`{l}HTybYz&n-^{1X?Y?1j{PXTmE{SB{fj{Jf|BIgy)e)(TMn+*mPsBe'
    'EP$HO6|m%q6KU9y0;$GBz{6)Ov7D9+p|4iJ`Jhb%RhL3m)L>}edz>5$NPx$dmas!v4y;RJVR()*;n$=@E+7f!ziO3?+4__8yE+ey'
    'pV~70p|8lk6=`sw)|Net>kIEXa@4xMy|LAzg=mE2K~T*QeE)VRbR_0b^mrrcf3SqI$7`WpuN2QtPKVRyBjD9ODNamCfU_SHVd9-L'
    '_^oX<<W3HPOXZDday=DPKEy*)$O}AIx&^W;ra*74@0jVb5p)huhveq3=rj8`O!N(bBqJsMYWP;TI4A-hzE<MJ+Q%W_pf9MOSLXBn'
    'B|rk13bTFMG399>Of-+}@VR=7&mIS#@-sm3cO@>dFo%PU9pBE#Y>b`wnXC)k2KV=AqNRBm$q3pAn?gKT%iAK7CBFi6^W=$dL<V{K'
    'YauMjSK(`>JHT}BnP6<B!pB@U1F9bnhp#Je#S`*y=GHQ3QkUn?o}MOEZ&yIG?jNi(t0aDNGokCFKRD#$SIMa8ELbz}G5W9GL;jg='
    '0Lzv;X#C5AwYe97B=R`^JGV(Pt#Ti<SCnJ5QVAPqunRI~q++Z0Q)xzBF$}g_gf#Rt(+%DYaviniUCCCaIbs8hlrBI})WmTM@?lGm'
    '0T#G)MT4uWK;mVF8~Y8%%X{NtQ|w3<JVY6<>r4dyzf1A@WC{M1rh>oAAuRbc6#pE_0M&wej51Zig~6#{7xNPzS6pOTKm1|un>M`X'
    'u$*-<nFfdLy7FD~OPTUnH#obtD^JZ&X3H0az@2+-IMen8ll?myLd(A3qe4^E{XG=Ely>3c@BWi)lV1rHrZW6*&@QR2-crz2x{ahq'
    '4a*;&3qQ?H;Psa(Sa5tjd`A_YuaYHwkd*=lNBqI$(?fthnGfeI9-)W4IyhP7!2HT`jHzxRQQiemSDA{-&rc)HANNARat(aHdH|uW'
    'n;~eT4Z9oXL<%Qm!m<=~Que%7viHJ#So3QbERH{Jx4>!%*cHdappG2Sdf!aw{eBDR=gnnjkB@_v|Bvs1fa!@i00=k$2si);H~<JZ'
    '00=k$2si);H~>jJz8}p08RIeA?_{&qLD)M=6-&M=fPf!@fEkjs56i*muMKM6915#sm%@f+fJQ#fu<~pg%v3YPLM0#QzF;Ou>U8m`'
    'Boe|J5@22IFQ(lb4Ia~dVOq#vrm}f94D1#N`HGB1{TBm=;|GEy{W`<288Cme1q968%c|RAAZ4~WY*DsltxFPMy^IV<-#4(yA(LUi'
    'pk}gf>jmlU)*yJ{^N_SWyvWj>U15=26;UJA?7}Q3=yj@&e7vrV#?jVryZbRRtfZa!&l(ET;#J9sYd_eY!VyrLAwy~(A7d45F0lBn'
    'BU>3(%nm(Dgr)=~Vt!qZ-E<8C|HffVZ@v!GU9}v_cJ?K;O)I56c7(&{I&0>8QcJR{WCes9YvbrD7pZ&BR)GEO_<d#%I5d3;xHrkd'
    '9^GyjIesF%sp{FW_lh{IJsd0&RKa_@DL$DN06H%XK{?Y9cis+%-+zq3cDxtX6;FgZ12^~{?1n1wVW5L<P-_)|YMTOJ`o~$&tmTde'
    '3jLsX?^LKhIRooL-Jo7=0j$^^j$`)|I5H*ycK1%hzz4%&XkI)t588pdiid+)ts4|q7@=c&6x>>E0iN-HS+(UfkjiU;d|?CgTQUP8'
    '@2`M8+Il!9e>B8)#Eu9<CH&coLf^bhSm`E*FW>pXu?smcB<3n>do&K3vsZ%Ctt)KCln`j1z6kt>o?)K`M#258V7}3|3ik5Ylf64?'
    'lk*;H!R~O_Ng+p-2sNxksB<MkohuP)VTn+KNQ4?hBINB7A#a!5-x0<0=H$SMJ0m1jU84BL0n*N#t==h`Pw~p>ycWhtg&I~W)VWf@'
    'FHrCoCVab@fL${o2VlZ?p9$Z0Cg9#o$P<{58!!PUXSa>E!qnUuo!@=o+l|8aoe4Pr6Y?u2<Wx+^wV04!vD(eQ!79RB((i*li+I}x'
    'ze1fQ|MOeIeX`)b0{!rDMrZwg$4QY6OHL*_CcVhY7wXi__*>`wNdq*fddL@&bhIn^oUcp&<7WR``#<SRZEspY>Tg|QZ*M}&o5y$F'
    'kNs&(WB&QV<zx-=e&0~a!@}X@NjVZyIhbaKMMK5xD3aa;^z8X*pmwYm3HoYJkLbn1gX-nP($$NupArvuyF8WbdE-s>ek6dY-6Udr'
    'C4gQ(z5t$&elGFd7DzR;7ebbkC0VUJiI!bi0+Ta(kf1X`^iBK<_+TGP5>JQGVMZBnua_q|qZC5-FJBF36>>>1OratDvmrb%gG_uA'
    'LcJB&fzPH*WaxiW=;}4=;I%~-Ss5Hk^ZRXqQ(Bvex_%`6ey#u<Wmgm9`=QiRe<#@WT21C|h@`E?JHSAG6{+79Mqifx2iK$5kgQKr'
    'saIPuT<}aI=M%%}q17i~K;m+8V8k@K{?#FHw@D%wCrzQw`e#8c!+{+8K7;DnoC2jCPGm*>EE@fV!55}Q2GqvU;ruuZBJRYzWG;Oa'
    'RS8{GHA#I_JbifKB%I!2LIUQ@r!TTk!-|%3l7}CX=zrJBp=e+q0wKv%{ci<m^tvXIW~We@C&xg?T8XS}T|_Tt9s@~HgJja^B~))|'
    '8LSQIPFggV(b!-ALDA0h9rlq*w_GWLO;Zj?^xc-y({`nBEoGAJSns8@?QRkD?=!_#7$Y5Mvy}G!xETVD<w$AYrSwbkcJMsYlWCSM'
    'p&u<a!uX3SZ0_YnRBuNC^qA_xKE$Wc>jUzkRXUdWnI_XN@3(@_lsSx#PokdZHo%8<DePUBxpc&+Lb&^AHOpU-Ko^?k!<icyOz!nu'
    'de&kStev-xZA+X>4dd5CPF^;fF)fBh1#N=Zi<{Z`^x0IoVjaA)SkH!;O`{Eeb09H1o2~GkNxSK1!}Nv~Og|!uJ{qtZZetqjyJs2='
    '@L35zdnB`wQ>W0Fx-{^+Va#?m&ZMJnXF$L84(zY#4EiH@8NBlC#+-^{=r_p{&_DQB`a?UKI@v6SK5|9UQ(tD$O-B~O<v-!lZ@s6{'
    '#>FY%Obl!b7R;t$-YM{_+1geZBN;t)E`42;0!mk$ZM6#LQCzhcd}J?6mY63|Uyn3c@i0=-^TK>u=ePp;HyIGU8_9HsPA2Sf+b20R'
    'B7xp)?a0eKOi8Ut3iYhYhRKeXCDr{F(x>OvfX7K&ayfJ{HOg8GFU&qlgf%C^z7Szwh_H8LMSBYE^=k)w8zxKsRxPG~J{Lhye{*8L'
    'H<^CjS_(&XyofMosW4}$FlQ#rSt`t#33HYTb7sPvrRQ}LXlYUoOtzlKY|Q7<d1F>V(e>eMhVoomd?N=cx@Iyf>)F(9#wsZAq^$Sq'
    '*|eg44K$9*VrgM<RQ7N>yjnYi{pz?s(QpSS9m--?4$Y#;27BRLeKHgLmkB=01Yc%?|1z)C5b8Vk6pWmd%LM;r$;X4~%#^E;w;+^_'
    'dN76R-MkE2Yx^<N+F)9H_W?YepvOksoJ{T29)RkeDyiYciS*}!H*o%$<>*C)Q|OUt_rR;~(b2*f$>GOSY0kOZ@X+eg=n_7aKDWOK'
    'ZMV-zKEIz$&HOLGE3RVeTNy)_Y&i>Qi;hXuXUwH{)Huw%qi^d}J(n)%hOqctnZzV}J`J8K1$=5@yI3iij;=omw%>^Dx1EdVA*<uC'
    'r;E3(;QLY`K1hZ5z=RmW1RG#N%wgA;B+}HZLm)RMoCz_C&3rbG{+e|JYBQ%YA*Qi{mKdsS`yYI{l){7<$b>k_ik8f!(Ps|8y^qV;'
    'xIYQ>KkFi>4PU}0xF%Dtx;>D2sV8eXolIXV?t%ol9!#)RCfG20u{MDYSb6{omEzftge2;}s~Cz;nJ^*VG9kt?A+Ab=SSl6vmk9ey'
    '?(jgGn)VhJ5~<{@R{(vt<Slgh&y;N4=1;Fo`2u6~O~^u3e;O6=6?X25C+`k=(Tv6I;O;w&#6R(-BaXJi?EWjsp{8+kW1Ip#Uoe?e'
    'J#wS(Cdtv=w~EMf4@dgmMv*q_t|PN_T&R9ud1}*MMPwWZy_uvyFX~ki=?X`x93(^IH5-Xlo-Hjl`vYBeH4y0~O3xR6f$v(aByq@S'
    'dQI^?%+YvG6trw<&ZZ}jvGFM}cCe=5W1fTO-e=_Hh7oj6%zfy8=oR_$XBdqux(9`_%|s=6Bz?H-Cdhj>lLrs2=uz40AbaN%u}Zb2'
    '1uiu(#qc$GH^`dGZ8`&0d2QsVn;qQ{!oj4unP?Z=(6GKIVAZ=n<a!{bZrx6SyyI))w~Ww|t|hSX>lY#uIhKwrJ_66Qnuw>oBV8X{'
    '1lLx)AxEBi(m<!Z5M_Fiw3K*L$L@vj@YDs;bSIE5aqjTtFGb{!TnLq2bQD5|7ZC3>58D5l6tZVuClkkb(?e4bKJ~gp7IpWam!8}J'
    '-MD)4(RczK=yC-X_#GsVyZTbEt@Th5hs176Ku0{k4aa+@lU^-;v~OS|ygph)JaYpnq&|kpW>ZKnI)RS5^b|sjRuQ#3<0&a@hEZQq'
    '$#Wb}xz{_Gmt08v!u)CXTc5yb$3C+3xgR|p{s9slkCKJ!eQACFU!a{^Le>oPq0Py^;PIZ5WVn(iy%#4#zyCziw912qB>aW?f-7XW'
    'iyM8aElX{G-5{>FT&eD<zp$bC4mrKgnMMw4hpWe*kgOrj)a_^+xYoTUQ)?XPr+uHHrsX49_}r29`TH4SkN+eKg2&R6$<JYX;z#0o'
    '+=-Sneu5K6-xHn5F4SoFC(s(xM$A`_qq6sZK+g|P$$w+rXiUUU7=G?H$+5Ag?z^AD#aAuFFUyw7cWngS4G)PB_lOW1$=9LIv?#s`'
    'rd)YK91R`lF%N{_mM=+GnjanG`x%DoMcD}WArml06fj06;E<R<w;rU;^T~9hTIMqB7IYbZjZFISn@MKAhB~Vcq>0^TQvI8tII$ZX'
    'kNd}3l$&7ZTVwFGddkM-U4k95!=e72466OP1L?cxfPu^vCY^8wdLEeq%1NKtg=H0RhUbEo?hCe|@HAYjn*?p1s#rdx3{G{=0fq3t'
    'EQlP3-XEi&qE#Ee%s2?PU$P;=SpiqI9EL}ar$K&$5grTL4>q^gz$d1H0)C4E#)|^RivkXenm78wO1YJg{>=fSy)|Ii-7>KA*TCHI'
    '4prX=?uK>YDp)p6UwWyv3ZnJP*+V7HqN^BOEIGiUZoA^e1?NF~M*$o4t_L_LNg?p&OD5pYOu(P<*Ml8!?)qNXJG+?`dmVx=tp_^l'
    '@ERsLdlf32Ho<^@XPD{U7P$K-9kNZ%vm<%mz;fsqSn%W=8x^lid*wwyP0CRgH?14pzHvAh6m4N6OSEaUZxFm`+{`{Z_oiRJjs>G*'
    '2~1~%G0l7v3^~5DS@9kndfmnvhAKHSp+;ar9l?ZJg9-HrdtvY$Hig`iZ0131&uTe3uQ;2$EpTHux3@yi#o@%Y_eQp0=szg=T0?Rt'
    'XS3mf&7c;2f{Y6|&b9}&L;A-SQg?qho4Mr|l=*gr{E`ZGE1^5>`OXwxbkAjT`}Ck2l5}8C(mWO!sz#3+cLk685+>l=OsHkpmXpKi'
    '#vu{lU4QeWP|L7}!9b6e%z`bkg*L^*JZOw>BDl|9HoEHW8Cbf*1YX?jh9i9$#9JGK(-t!<TyX*9Wn@9V!_JdWak%td2JX}kK>?pf'
    '0mDZD!$$$<$2sA9q0ep|^4TXG1^gBTj28ur7X=&`1^fyH{0g^g=E28r#VpuqEDHDl3K#+k*a8YT5(<1R6nI=rz!p%z7Er(<P{5Z^'
    'z@SjTpisa}P{2S?z*tbgUQobWuq?(BzMhW33Ax@_pX>>34ry3=$`xm>91Xo^W@5!lC%n197gp64Vfux!=&oZ6hvyWbV+x?&NE@iW'
    'cpN_(+Tr23W-xT$ZcJ~MV1ENk@L7EVqhS=vHT46-*5mlPdJxuivx2JVtN8HI5cFO-2pr98F(=m)P0x-7mwqoX?(7JZ`i}%3`PaC4'
    'w;`?%7zMF4ztMS|F%IbE1fz%i!iCjc@kTfSc?)^IWx7hoGbg}cukTneMIPU$OoGeG3cS6k2S)Ck10TBoL+SVKcxl@rNWG`b{{$=G'
    '+9|8SdvO=O`n?`*G+YaR7pd@?^@iv;cr8?hD09n}As9Ge6C6tI!9QB+;~}*IC~D}zcfYp7g06+I$5V^H{-}r3%!@#0jW$<#?ScaL'
    '3~#j*!dF{OzWc#s3_Gv|vXZoUYUC^w_-rWf*-+rTp}>_wfh&aq7YhZB77DyF6u4w4aL-WSo8h)@5-6I~j#H}vRX^Lon#(^hJk|j{'
    '*XKiTvmX4+4o?*Lcqs7nP~h*O!12SL@k=3ia62X~?1KU)5G9Ut;jncJ=4Wc*;oY;K@0upeT+|!0eS#rRuL*MxsGz_(#OP>mh<Sbq'
    'qtzAAYtdM6Id~XDKmK7!Hug}^cpi^V=!(5B4uf^Gj^N~MWlXqX2tUUi$Ms3Nn5|&}0}FQH<k3plxLF%iWp-mf8(n0#l_4=;C4RZ0'
    'hnJ7`f>HW=Fj961>K{;p;eMIe$JVA}o_Y{7WEF1pb-<NI+MweWgL|6Bp}yP@D5<JJ6^*_)&PM{tGSBeEQgt+V;tO?dPjGBQSIi8E'
    'hNNyEu&PM~1+F6sd`J{HlPGX0QQ%mjfOBGMeiYcJrs3j(vAC{l1nhO&jh;bHDDe7F;PRos@k0TxMgcEH0WU=XFGb-j3}f7mLAbfI'
    '-O<_hD7W(j<UpD9*%y8Md7=usrH4rzOAT<#f+|=Py+E4%Lmq{5QdH=O+hwyE(L2^1=O&+ox7(FikgGgy`d9-S;fhqf@*e9SeFEHW'
    '4u<+@2@2=7D4ge_n?^qfv5kc<Nq*RL_PIpedKQ#?AB)S*ES0Ek%7*kPOFa4NCX*ep6<%C5z<+6{ScC6DF#q|T6@4L?DqjktT~*L{'
    'x*gg(RY6QnJ##6~L^X8=%Vz#&Usq(|jf9J!f3=MLd3G3O_Se9+oI6b5n4!QuLxFFGRZ8l-_~&3$JY$FD`*iqm=}<h9Pw;%tUOdPq'
    '2=!(U!peL--ak78ueS}xUc<Eb)vu}8TrZ18-3)o8{UY?tP{reI{dkdKHtsn6gq{9u#Oo?n;jo|Y**k3$etUNTHoSew=<NYK`$`sG'
    '(Rs_f)(qeQ(Od8^f68oTTJQ(6R^#OSj{luv&Q<Pi!D0UzS@9DKp68o`K3SJoMY%bbf4L2Ne!0xji_N*!>|9hxI?Rgi4&-rV+i_0Q'
    'DHdgI#xpOh#q#Sr*wkn<u2NKpgEY#RYMv2K`&o#3@h8|#Yh!*+Wk3FNImQee4EfULeVF8Oj@>Uc<)yO^VyIIMbNp<`Pox%MzrS~x'
    '_E8hQ^UiMkv+5a}G0u<|2W`bZeIGEcK9En!--9X(AF~6E=G<Pc2<4vNWt#?B@L>6U*y3=B{Tgr1A6(pr8Cxru)+aMQqoNq&wMv=5'
    '2}I#63<VA$3g==d@C;GlAELlZM1ik}0*?^|ej^IJM-=#wDDWgv;7_8!t3-isi2@H31%4(9yiFANoG9=-QQ(4N6K#;R`M99(ucu7l'
    'j-tRXWdgqx1r91M)b0X(=Q*NkDn(+}6@s?TM*kmUP&kW3;fxZ6b4e7=6Hz#4MB$7Tg>zUG&S6nFt3~0Q5ry+36wV@1IR8cATo?sj'
    'B???h6gZYB@G4Q@L7~8_M1d=X0<RJUJ{1bQN)$L(DDWzoz{_F+UyBJmE@rgFpSO~mpjn;FZnTB)+uAjqX92=}a@#D7Pq}{)-mIBU'
    '+yX=S(VM5?&Yu$U<83Hkv*a-B(>5ccGeWu6mHn{HYy#O^7|8ovDd~Jp&euRbN2jp!S{TFL*oE@r@!MffdNMn7D1^V7dl*XhpJ%ru'
    '!Mx9<ouKfqiN!DQ<zC}TAkn%j9=+<#VcKR$-=>9Y`#JONV|GFL?%`N-!h`#7jR8kC7<Y0<UOp=x`Uf~5DFQyId?;w0o`3?!3<Vx6'
    '3jA0U&hc?m^*HXDa1uTx48T{FZoK}|C3tVAgq5kDJj(eFNb>KqIwyZ#{O1&;U;4lfeD~)Eoi2j2#$_g~4-?jh32Vr@y$j`Y6)HN{'
    'MBuwJfd|V3t}K=pD{z(dmqEd>9}1iYR2cIb-yS~?Blp;&z>&b&qhFwn%L(}R!3zaW1+HFl8C9O|gxXSD6gU`YIAtHc)7TAH$C;qO'
    '*}x|a(@~O}1FvHM1&#++`k!E1<>$hBxd0S6A!z^MpTu&N0rbzFfdYpFD-#AlRm?zeei@Ad=L7{F6bif)6!<DA@K{jbN?{Y^qGov+'
    'L=r8GE;)uDe<IB3xOTXI1!ZHe!P|n%EGeZD$FDpNew7Aj6mSE>>@GuyLk~QyeHVGi4aiu3gEgD~z@WbMkYaR@9b)x3)&C3(>1u`Z'
    'FFnAuKG)#+R#g=E%qVc4QQ$?Rz)L}ai-H0d1qCh&3S1Nv_zWoUQc&PFpukZ<f#-k%Uj+ru0}9*~6!;G)@E=g%{Gh<|L4k{c0v81Z'
    'o(2lM5fnHoC~#Cz;H99zIYEKjg985t1&$C3JR%ghMkw%4P~e}Sz#Bn<KaT=u9tAEv3jBGz(>j1}T&PRN2B+isi{?DS><Yo2OE9m}'
    'h7a6&is;72;hwS~e91Evm{Sywzr5`@%F2QA+$a?IEhzARP~haFz{$rEm;3R`-{$C>M$kgrl=rds$HqN_aliH;UiB~qhqm{`_NPPn'
    'H_sKg{aiP!zGuxPV>jS4t3kLn%!Ysaw+T&Lb#U$Q(R`rhe$4k9h$VgOc-Hg-=(4yUp4~Bq@7Zz^cg^g`|AyG}5w(^0`HT_nnr_E+'
    '2VX^nqG9-b7v-DY)ne;RGc?t*<MG8W@kOvT-f5)#<*1j~lG#xct+M5c-k<POloi&jmhfw)Ur~p5<Sym5yr`EP?^8bz&AlD?;_1Kf'
    'JME7yzkz?<sK`UO1v=-raEp^&_z!1OoUQJ}OAD2`eaAQ5#m|io-lxc|yvE?;3uAfOc}1>v&mX51xpL$CT{`mGP?UFd;!VpH__{?w'
    '__x`GFSL{8)jL8kCC-7L9In6vAPnDiJd=6<#>ownF!GuMFVy{oA(O)~`l~a4yy-1IiVDESYDfNW(kuKd<AoXXoq6%pn>gjPD=KO`'
    'aJixzIB$&)rhFL38~#>w)MZW`&vM|y6Hnmn7%wy#?8Z+m--YLlozcX7ET1-_2%l^F<Hr?F{A$B0T<jNs|C)e5Q(l96T!OKEl!Rw4'
    'aKalc0hrf3ig!=z$f-iYkUEd%e}5X{efP;|RA$LbN9y42*qP|0K8mZ`Jz_8W&A|<)&A6-g5jMkT0gf0qf@?RbGVR)q{M*lrE0{(}'
    'KVDA9<#{7`mi&52miHnQbRsBdNpS4e!Q80dB&^>x0e?>!&M)`{;|cXpl<1G-?~bg+A#%?6-+o(Odo~9%lP92Lj}50s_TYij_K3-L'
    'd~<yfKFs#Ty$dD$e!(%U``MA3#yaq~Pl_;Qz<3n2Dk$h#Ftf&-%e<e6UeykG-^hwb9?U>##R$w_Y|C%$I*vN>4%m&1;iKGZF+<iK'
    'gW4qg^Rycn;o^mrEw=ndpBHGkmY`*o9XHW>f!-@U(PRE-URLxKue$}{-O0e+6ux7|kU(rK9>cYr<#^DSAS~6Qyz2sa9@{t>yW86F'
    '4Ly~3A;#cbMtOdQ3Ri)d_-r%b2VHt_78H;FnL6^^!QHvv!$=(P!k(W=(%`3X7N!?D^633N_^LE#oI1{t@BY(^SL(arq>B>%FHVbR'
    'MVVsH!GxcDsmr@u^~QS%w%qhmA0Bwk2nS3Y$)8@;;|V8xaQ^w>yh6P%R}3&k^S49z71ZOGmW{_hGY9b>4|Vz4jh1L@Wy-JJ@6DZV'
    'j7HTL1NnVb4er&|7OOuD;Mb;V@P8L3qH6sh{_=HKzUqoQUOGC2+mG(X`?`c<$iu;W@C7A)c8ELvnKg_{DinETT_|2!V9nnjli@*6'
    '9I@)a2<}!c%a`Q`VE(dE+<fRateEA19}igb`bZ^C6Jv4jS}VTncURu?O&rEF+wkV&-MPY<L`>>CoSPN);=h$wpvulM+`n3jmmf;Q'
    'oH3*Mwpo4oWA%=G{YJR@zuw&ML?Y^T)OTZ#tMh(KX5jY`gZQi#b#C%48S_q<@P3!H`QOSE%;_<JpOEjv=NhDA#Y0OTYtWb9R$hr)'
    'caG$DjAi+qi6b#@;ZVL%MVY^;9gT)6_Pk2-6_&=iW8D%rK4qQ^FEXLn{j&>y`uq<vk1#a8;KqyfTkzYmjymg>E8jl48L#g0#Sl|>'
    't~Q|#pZM6}ffLR=$MrAX-C>5o_gwfj-Ph<4HVFGo^5D;(-^7J6Ryd&2g->g~j&pttL{on+K0-!{8a3uP?wlK+?pTSTu10vR(T9(E'
    'w+mP8F~!`wUi`J<E_`#QH?F$j!RL@w=zCZhuO^M<Pdn<|)EO%HTg{a-5`m5(e^}42lm|Rdz^J%3=9=ruH{?w1*o*&IkM5MOe3^{T'
    'Lra+DjB$KWZgeM)=wl{uty77e*TNX$UT@7UcBXgUj~qLSPlF6Rvc8N6^)eA^Y9iFsM5w!oP|p&f&Lu*POoY0a2=y`%YGiUF&w#hp'
    'ZAZB$7s&25ea?5};)j|uB>SoXSB5;CJF0|e4(!7xIjrfNvrxYif6sy3zif5qePKKkp2LLav#%u`wpP6cN3A`@{HxV@S;ZQ>c;^s%'
    ';;qIl3)bSa0lDn6iW+ZPuno21PO<OuJ@|v=g?PhZH>(<?#-9}I#h(@xZ1CV7TzPXby5#L-s~2_U8SW+c`sNX~&bJ%?>9r3}Y|CTM'
    '!j!l{=3dO&xs^3*cH^t9w&T~9b?myb65kiK4JB6F*;UJKe4#W4<22^6(@9-;_O>-BE5EX1&VO+8)6~xQg2{6H#?)1qx1^Aj_4tLV'
    '-In9R#GR}(=?Cs_pNlVQTUk-jE4;rW34123VQ&oI;_R46^h|GME7YH&t4kdAzI2}DjCq9J>*Mfdb1OTlUyt^NNx1*)6BgQ0=dOG{'
    '2T%O&j>A1`aQwMMJa(gz)rOwO@-=aIt40ykKUCl{mo)qkqKK=tPNF$W#&g?x;DQ;YDA%?e=T&IqtgG8lv3mxl9M?wEi@De^c{%pj'
    'VSr<%r{n!O85o<YkG4T+cs4Z?!wep=@%?7wzay!rnQVv=`z`R}yyduTb|Y)wFaVEsO~jgadiZdC1XEH7K$k{&3_Z~xA?-eRe)V1!'
    '*n0-+**p{b?<-{2lUgPBHvg|KwZtKf-BO9~ycWigy>3I$w0|ak4cJ74-y*_%h%g@z<_yBSfbfnWygQh-mSWJg3|zYP91+$Eny#P1'
    'L)(_))r?9atSwPjtHn7o3$g7DBf?$~?Jf<NP?v<`_Z}g_-VtGciLk#!umKX4(S}EU1mkE&9oW*U!n-V7im$H7K>q5kd}qicRNG|)'
    '0xkyvb_W7>2LiqaLT(Ad8nP|TOEEKYH5v{oV5_%}!n<@;=bDe{lZpm&vpcVaG345v5-j<*@_)6%^GmU?d?gMsTTk4(-oeG+Qm}qg'
    '7J2;X4yws7{=Z|Gu(nKCPbRD(6V{ChdSrIh?=pGh82o=V%S_NUvoAdf44*n5n{DM#=qG?eKLHea2w?Tsx43Ql!p>(3{wTf+J5$`9'
    'PoI?4IY#htBKSBF{F>ZpP~e}Y6`+FAf8@$H1@1Cs6((>_BFYr`z~}-riak#Z@2l_)WHVlT+(0t*y7GYwcVX(o+hnSTD&P8TE2jC@'
    '5Tk{v{7Rp_xTWL*5#ksTViyr&8WG|c5n>k+Vj2<R7&&a)g^%908*K(1Btje`LVP1aEG0s`B?9(K1WXtN9GD0-3kWzc5wKq(V8TSe'
    'jY+?iwtVBFG;Ccj1411HLOuyXJ_$m83qno{Laqx!ehWe#4nnRDLaq)%J`bvqj@;20F!!4TR+qYSlRcSO;!EN0b2t9sav=Vz908{-'
    '{CH478fxoU!DBTKKFY=m%S?xW$yz_&^=umYWoSW_t|zyP^uk-8<Uz;>h>!yiAvYiouXyuRIWJriv6CDr@Zw=gKAm>>eZd6&xP36r'
    'aoj-YNq^q&=g7|c84H8>u{A1q^6hexA|K3?<huUv{fi-dRQ?r~IBpSH7ahWb=krdzm9l#X*RqOY&rYO~#U>$quUA;-{VBl{d5>kQ'
    'CAHNV#Ar$ozX@rb9OG7L0AG}~nf#wI%%N8RH%s0?vgt}@85qcmF;8M-zn|r5kLRuf){}e5rEJG1f1V<Pl1X15u<yftdDNsFa>%`b'
    'nJ@F=3W--G2R6wg-{`}QT@%T`#cEis>cs;mZj|^&^u%4t9=uw6898@$4E7Io;UVQC>@NJV$1A;n7Zs*UoIg!P`L#}bsIxtjF?PXQ'
    '4TRhNv}V)u!f~}O<$Ui0rhd;Cb(CCqyGt~CTh<rnZ1v_>8p7C%njY9sJ%HP2O=J6y|7C;E2J_yP(^-VlVJ55(6V{Lk>&%3`V8VVe'
    '7mx8gxoHSW9zJHmzT??VZd~c|NZg~{0|h(5s9M*KT4N;I;9wN&4d+&l<Dre}IAO6h-dJSMTiXmU$HNH)J4C?_QLsZ4Y!4rd^WkX+'
    'cj4qSqcDA>CpT3+iPfQFFz8`0KN^0Wh1ypzdG#RPT}c&Jdt7AY+7tM7n+CRTh62_(`EmJF4Lnz^gzs0o^O-$vvVQj3*u7yKFL<De'
    '_7D2t*(**wP5lltUoXM1InKPU;S$?%!2pGIAj0#B@Vi7<b0Vw*2x|qxZ-Fo$5at8IoI%)M5cZb{c1Q$UC4vo;!IQ`Hzq&t26we_3'
    '!zb`*TC$yZY(?yNKAaDNwsnh%)6Ma`Y^PP{{iV$l_|bcT|91?Fn?8Z-Km^qHo5W%?g81!4;qdMDUWQ2loVuq#wnrojI}*$_7iPlj'
    '>Fb!qiHZDJWJc$6UhSI5GdBLO_CXj!Dz!p*Zqz#PHC;;vFX^zu>|EgEJ`n*MCjuT00!|JBHVy)g4FWa}0yYi;mIVUF1p@X30wx9m'
    'Rt5q_0RoNz0@eWn1_FX@gRuVWh=LMN+_D=hAD<y9aVmUCbtdjObDwN;@4<im&Bm`|E)XIAC&Kw45zgj_P#-akA&z`t)C=5o!VHVv'
    'I&qsdH*njV0r>2Y6aVtP63@Oh!163-o{>|G3WKyz=<k6-4u(RWhC-f(!aSLf12Eyc&xCw{2|0lHzD)Q=Ga;{F0k_WJkAQGocv26A'
    'bznmNz=ZsPbxZW;GZ(%ho;3%UqE-MOy2}vy9J|Jj91Y+%l&67yy)p{6#1=RD@uO=@;k&LGs_pdWJ>{O07n?sb!*^c%v3)aX(inlV'
    '9X|f$=tn~Hy>ZzudwyZ>UJ?=!f<Me%`GOP!xOvb41zQ!*bck@KLxi&uBAk^F;cNwjvlY^RNg&rA5Z~z+f`1Xgr-<NdMCeC^LO&uD'
    '`URoTM+k);L>Lff3%@+%dC5PDo4^gqzsd3ug%T8cC85wO359-2DD)aaq1O-!J%v!{HH1PBC=~iWq0lD^NBtND@;VCqc3eN4s_YKS'
    ')D`*j-Nq>NbV8x;6AJyHQ0NndLjNcf`bweDCkln0NSO6uE!_0c;Z`Tr(6%e(-*XP2o`*I<sDuYC*?`TxRZ+;<Q0T{nLZ2?Yoer?;'
    '#7>l3)5e6pURdzX0CGwe;WGzC6#7J=&?gFoK2a!W@le5511>d>!@8AzDCqUDWQq*vo0#L0->xX=`%usuqM%7cL3@aTJ`n{SA__W0'
    '6g0CaXcAG-*rK4rML}<iLQf<V`X=Gr$xUR;R8w5SOi|EaqM!jpL7#|%9uoy^APU+{6!e%V=rmE#W}=|+L_t%D?H?N9gI^0wsA{O1'
    'y!{@ePjBt?yG34~A;{x<=e01#ZqlER5c}pUytAJw8NK}x)Rex0QkyPh*2T~8=kO<3n*K(TYy1r+@u%?Z<}|WAQ-SiIE%2?&Lh{@A'
    'H=J190Isns$mtv<YU0-f5i2*7mY*v0@6|e(w_!I~^;46+m2H7URz}`A>d+e5jyc^tP2xb8&YRu>a>b0y{B1z3W1fP1*ePN;Q;$~m'
    'ZUK|nyX5-;BU(sbfX#zvWb#OTI_z;PShu#3&9D2>^waNwE>wfr;eF|dhri+NC?%jP_34x|ZIG>`4M#TX)5@K)v|nU5xa-iL{yr;1'
    'l@IoZ(Zqn(DJszP4;pZ{#gIN+ra-HYn}XwFGx{|~k?yM2f!9Ng>5;*T)N;Kwgl`*2KU68x!lQ#>$+`jb+q!Oa^%-Y)+Gj8wyH17H'
    '$`68teJrWAZFf5Qt~Y#sGl-s9r%W5Jc|vR-3tID0g<4+^hY@Qmsij1TZnE-%v@-+g?rthnQ7HmU;|9`g)4I?<=RLrqZUDu_iqye>'
    '8XVkdN}Ha`(0j|mV1A}4&Crpj8VBOQ($0jcd~busmS`B6Z$eW|WN75)Brxl3LMwOt0P~+q;O{zPdP-lGZtju^A^Jx2gryA4b<Bl5'
    'tBk3$x;$-l%z_ol#`Nn$MXD>819N7X(3m5N^v&Wdcoo#~yW6_bNB=UxC)|{drONbWWd?Xj2T<czUFo#O1UPzn0F^COriLdI;SM#Y'
    'f10|}D=`znX}TG`uGoVrub2-?|C!QW9nYyS2!!f7BRV`&g_aDM4|Q6G^jeD?HRv@R4!ky?8XvmQ5UX^!HMT!plk*E&U&Vlro-r+X'
    '_8DX<RzQl5DeXT0BfQ@@8!omQ({T51(2aRP|BiWjA8UuNi4O4j$3WUHm7{TY#z4%*L9`}Sp8BPX1cyPxXq}}Z4Y@P|yeo%M8L2F7'
    '%rt?cD=cYMpd3AK-UYPcENSXRMe3NS1%KSk>2|p;ba;zA$c{9nSwp)}*NU$2JHH?OT&qA0WWJICYjtVXN;&#5=@S`tL5I#g(+)>Z'
    'wGf38BYJ0EciMNxO4t%$K;7Mx>8V+{a8b>eK5$T^`4(<)ZL$HqQ!YzS^>Bf0UHen^_YWwnb%L?K3}{SWS-RAG2t*F(PdzMuLw`dn'
    'n7p|^J=XrN<C{JLvL5uO>Vfa!slPvDr<u~Xl4p=)GZ*5ldQ#iNvb0O|65_m3o=&y@1$rr}q%B{AmTp#{cg_)#vP7Ob{%Qv=)!mZ&'
    '2i56=Qbnp9^-f}DqD~)2D%1ao3HF6rl+`O!QzaYHwxbu___J$=kIkr@xuC<Ra@FX>8Sa(B7$#BeM{|O@(+lN^?CM}Wnzu!n-uk(o'
    'S-SV98!S|4+lxYWE>4dw@##X#9^7Ki_YG-cx+0aB)i7Z_8O<@KYx26#HEZ57Va;*)yn!^qz6+hR=o=IE1;-Z*qWk?6Xx!8rOxQ<E'
    'OBqbtySBpyl{<`?S<-dtzaenYCw56;FqOXj3N>qPGwJN1bi4I0sGg#afn}Do;bsej;w=^#Ka?6oe}grrb#R`B1-<j}16*I;8x<QY'
    'sml7VuxGq34sA50Bdwa@tnx^_m2N^0X?}%y7e-*>RTJ9t*jqTM=8J-TqF}cu_$&&3ih}>5;IsJQuL-Rm*M-K*Ek(g+QM1{Eu255?'
    'x4LJd;Ik<BDGL6Jf}f(`zbM2X6k-$#F$#q^hJsI_;8Q606bkVW1)oA8uA&foQHakd_!JZ3IST&8g!s>dZv+#*5lr}wu;819)X%X2'
    'o;O}+!gq%~Nz|dH|IUJ4`voR^r&!L1?ld{`G{luxF>~dA5Pjq#6b~t6eeD$JyRS#!z0WarIP@iK4q(u)|3((mtr;Hd-3{Ht%9+il'
    'OYpAOF-SAq!>+X|(#kLEA?zz>BO|ovc+VwpNv51dMj2Ag!}0LQs*p|EKaf5humqkD-pK?lHXBo9MOCjXhJ}Z=FhPsW5-&Q?0~Tpe'
    'Vz!eBT5R^u!-snJ$$;%MS2971%>?~56Li^3&|)(|f6WY9rc&>XdEh=Xllg6&Mq__&h9h@!nV`95g65hDx@;!sznGv4V}f3c2|6++'
    '=*yU(J7a<#jR`t6Cg|6gplf4--i-;GIOb#{q1!K91^a?$OwdWOCty#1PPzx)=Fga*rDCab9qFOm=b(7~3lnr(OwesHLEFUyeHIh+'
    'SxnGyF`HHoy3n#C<{WHdhHkF(#@G)q=gk*3>a7Po^xsF=dEzCTq2^A9KYt4ze&1Q)Ob`05q8YXv|IC7~dD7T~W@sGuhGDfAjg5W}'
    'o}=qn;6ZO{r124k4Zp^2nEO!GidPWv9NFaEK6KveXVBwdIV%|9O&1+{23Oo}v8Il_NNjil6_Q%^JJgf9FM0yc_djJZu3q%_-TNTX'
    'y3cagy3=ueAHcD-uR84CgX%`s!`<9Q_NLmEmRHq7lh+$2==IpY09U%#=q9|{_Jj%gJ|<|*n4tAzf*z0w`aUM;{+OWeV}kCF3Hm-J'
    '=>C|X>tur7Q~EpDi_QxD3b{SbvzMyA6u-AX${r~b^nFaw05U-X$ON4r6ZD}>&=N91W61Vj^`}+QFF{lF5EHa@Oz2&}gq{XWxzL9u'
    'ZOw<5caJln2Ld~&=SxFeSAm7vPIh#WBQ1Zp9<Kd($o@RDrTcLkT>SN${p>M<J}WAQgywcOZ^RJVXZLBq3R(0F8B8yz-Gno3ZA{RC'
    'GC?cK1Pv(@bf!$uqB23R$^<<l6Eu%Z&^$6h7s*O{{=cTqJiMl}i{j}Zh7g$}gotQ`kRXPTv)9(B2udl6rsk=JP$I?{T2snrs-Z=d'
    's-lCTrAm9>_ZUh|DOw~&g9tGXEupl0dH84jcb`0wn=9v>ckQ+J`t3HFGUz_GTt8|kJ839OYbaxDD2Hp_*xOn|%RRw23+Mk3{X>$z'
    '^QyNdZtA{0td8jJFG_2NBd47Xw;F5FSYNH;9NRwp?WS6CZ5hqDn<DGFHPGV?{B=&PzqYq-(m)rz>aRb%dDz*%qK*z68l>4D2k+>8'
    'JXWjw1nKICGtS>lYUsMmpyF%&gfqQktZr``r1LLSkdI!7)~|*KY2V8+lJ{+_mRTO8EBxC?*wAQoLW6aC@avLaBUWd|2WnB?3|aMN'
    'wE8^>(%S>3Nupm(tsN7h>#y&WMj0>Zg4==m)5BddVZ+P%>b?-IGUG2PI#FHqQh?4bdLnOpR8u>f5dCCvWt=ZvOK<-ap!u~Upl4&X'
    '+NdCns}={J&T+au#a|z+ibc}MM*2#>0NtI}7^#26>(X<+TFFM^t)@+M{YpQ*dhlhuFf2ju{otp$Ei2%1R-%6VoxkqzR6=rCqP{&b'
    'P_KJcLf&lEQ`-adVeLpHN2q!(2WiyEDj5CiD~cAu+OJy`97=@Ny;?zg9u3EL#ea+Hfnho_KOF!4@`^^?si-BAqwp}Ng?3D?q$@8*'
    ';AZC*y0ufd-cF0gNBcYK`9tBl>RKp@RwnCzS>gKQxOy1fH%0s2t*FbtX$&n&()p*twBQu5>RwBAu7&FAW({#EI7#o-3)Oq0o8sV@'
    '=Gt{ykWNo%gnjQrr~e+HucaqozJGHq`);5H<isF&oa*`c0h)B64n{R~G<{Ww#{HtGyQ+bX2?^2tUnas`-9US+3)8bHO)=$6tj1TW'
    'pqX#h!?JA+bYt~OIy<Be$_$FrTO%uKc2G6!T3la~6Dw+~^e{Baiqro}h3Ry!a@d|wUwc<5)*m@O==*h?*0jO;i{DlGdw+e64hYmo'
    '-(Q#fQuQ@sg}>H1XJzQRcy0Glc|CBrNaBBu*YnHE=~r!c%kj1GS}(*$fAbW{u-)<6zIQ2I7I94cN7T{attGYVq<kSwE537UXwJ6M'
    'I{VK%Vn2)0?{Ah=ukpW1zIS!q@|>?Wn|D@fT#VGk#z#lh-61=oqx9i*f9)T6LVoO3O*=33)8K!;m7|BFG;wI4mOQ*f<Z(51N(bt='
    'dTDaDxbDk86QK38+RHn2t7(ndf!eQXj7+{4sS6hdYO^Bjxb#*Ht<x@8m$k05gYF#<-BTXA?>uzRdMG<@C_8T`FK;L>Zzxl5=pHwH'
    'a;vLz&{qdsekA|isHL5km)EUhs$$K)x;i$yte*TV9K+f-)FY|B8a5&jqke6uo}K>M_jw=Oo84Hi76xef_k(e?PeZ-XI#{>uDv68*'
    'jWsVnMAPaA!0U7a{bx;>mYf`f!MO>V)xM%WUQrp@-i`JC$%=aNU{zFVAsX8?To-yrV@|T8Bie-Pq527!()JZy(lcDQ9H|KtmZaBG'
    'iof130VQ^drWM~K=^BY)jhbpqzY03aI}AN0*U-7Hk1l)sJofLYqc**a=KWCu)i*er(Xyfr^G-rSdW;q}4Ab=o1JQMLjE?*uR1e)K'
    'l(Z|w&-~^=I(N%<`6sTvjt%hB`ekOxqSqSgX1}tU{=*!}i*Km=CzjNhG8?5Zs-8w&@Y3a<?T}W<@#;164w_Z|Q}*P>>R;gx5xeG~'
    'P)#IMHwo2E;ujIGQK!r6hVAdl#+C6pZIPdjtlCj>I=9k;tAn-dOK~_^B1Lz68Kf_ktOeo)d596@S-PZ?rk@>;i$Cv7n3dH{7nGcY'
    'J%#xRZ#PcWn8BIol=78Rc0sS=XF?|QNv=ce7a`t@5C=wx{o)W~M2G|9OugDe>*P*GkC`tvq4)C8dwKS5@YkMoSK`5-LuPGARek5~'
    'd?a1iZ4TV8uKTafLE_0h=AE^*i|^TKi2iPqSu?u6%A3=%_3tgF%={!3&BFDMcbc^mD(jS2zQT#6znfdB#rIKzy?EibV`j5d)5X2N'
    '#HRO8n9X0jtXBqZ!mh)&O~B_ddVj+r%<;}O<xADo@>iE)YrFd<q-P_I8Z!^l;(~dzf2@{nk%f<PJ?2{7S{gOvI~?2d*sQ)5tv7PA'
    '@$ciyrsJ`inm0EW(_g%3aI>~f%sh?ueQ%k_hqcw*zKG#z=giQoy1I5oKK@#B#nAO&=z1`8%@}uhO}(@9BAS1A%!CepNrR^TiATT3'
    'Tb~ZqH6u9>-npGE`45(S2}>T1C4a+`=VQqOvE+?d^4u)>Y?k~tOFo+=-^r5KWXaRB<oj9j1}*uAmOK_q-iswq#*!ap$+NQLty%JX'
    'EO~2|ye~^0ktMIpb}6pe7tPN>7w_}t#-k|h()IvKw7z7B2V#gBVu&kZ=-xN<OfYo+8hUOR(ldshEr#@rq34ewJ!9w@Wl7IiI!`T~'
    'xt7jcOXsqsXQ`!UprvQ2CCy+-OIXqmmb8bZ=aQx8k|kYXNlRGL5_U{Nl5R^3)O{zaS<*|EG?FFlWJx1g(oUB2lBKi2(s^O&OtGY+'
    'ENLf8TFcIQJy{2i3DcsKN_Io>>$nmjT9i}Kl6JDBD-3B5L)ycTJ~4D|S~@o^otu`<O-tvdC0%6c47H@AES;g2G?gVCWk^RE(oyDS'
    '=P<3;?*$F{cfU#45~{7wmeBaE^G#l#V6Er%AL>0>XUOw3)L$^vgD}*aFc)U!<GU({;B#r32`%?Cnx5MQ={3vvUHA%Pw|KDn{1=A$'
    '5oS+NsBV4qFNUWcHo+;i^{pxovG+>2O>10RE0^-pHGQJ(>7Q!o#=1|?FDlxS|7^*Zw&d+w^7AeE{Fc0Zo8Rqat-8QlJqIUP`s_lV'
    'UFiQu==T)zT7~>rAwO2gvz0lABlN>4AI-ctL;CNks+-^N(?zj^B=Dt3{o?~a4VyMYo*NsX-p~1K_9xB7lNh15hWYD>y2(4}>xTZV'
    'p`U5!=a|X$sutJpW%Q$xD-3B@L;BW`zBQzQSqB=@QI={bOZw1KJ!Pq$vQ$r5s;4Z~Q<mx}OZAkcddiZnv!oj>)hw236HB#;rFzhi'
    'Za1Xc4b_r{G`t}VZ%D%%((s1rSwl6fp}N&j{cEV^HKg&(x0%uU#$a!qlyu2ZonlD4TGHW`ynUg+wUD<j^fQILeWCuNXG_Nybj9u`'
    'PkWTqv+z*Q!b3euLp@3l^(YPXC=K;Q4E03JoS)BP)%jd}+GLP9G+;S?ZIX-jSE`sUZI+@)&piDdM%=QP9(VES>kBa!e<$Uk*8g4*'
    'dTsh$T8Y$7hw<(8>E_7o4{#tZ8=sV(Vdl?Xj6UVIBC+~OLo9mpS&yCAH1a4GrwugOi+7;IrGI6|m1O(FylEJe`iy};<l!{9HFNOU'
    'fO3Yo_l8*ahQ3GWeT6=Y(0d7eUZLlqkk>8bfeZQMLi$!n-wNqlA$=>PZ-w-&kfs&Vx<a~INLLH_-a=ltkZ&gBtqFN(LLQoshbE+@'
    'h5R&-t`_pvgfzC0#un1aLV8=MuOy_sg>;=zZ$e1>3H6>p+8fk+0_kv2?+MhCg3qXzbX5I+P-}cF=$t~sxi6_5avvWa2?w2PpgtF<'
    'M+WMPfzCcqpF*gYA;g#x>URh+sf2nWLJTXRzKIa?N~q5w#KjWoxd^edgwAxKdr;^;7197gJsqK5k5FwWR2vG_hC;QW5X(!5KL+BG'
    'fjA_fdmqF-6JnzY@xFu@UqW0j-i2YF^eKmYa{%LCUtwq$hPm|4akFsE@u$z0--23LPuXX?ISO{ZXT5%V_L_ElIJ5^uXb*_ct`H&C'
    'nGoAVh<PH!IT6ZqgEHMhIc`vnTPUv$%5)25=RtXSP}Uoi69?tWL7Wy4r$vb6BE)kOV!nZxZ$ex+5a&&Z9S7pcfb#MnJ{X951LEF*'
    'I5r@TjSvF|#Kr+JYC!B75U&Q5@dt4LKpB4!Hvq&I0PzPv`(K21z6f1=LOW}OcG)<zzsAYFT*e(g`|Q(eFKgUwn;Dt+^!4z&FT0C_'
    '3!lEG{W1>ik&zoOer8XV&3XDgw9Ce!9XE2?xHc>9*?CHPa2(o?BeXZip?x}XbIwuwVeB&vKrDJojCxD#dP|IYdthV<Gzfq8zO?T~'
    'ejFff57*c26&z)o?~QkT?)bYMR#mm*PuF&%OP6(D9wGM6W0CHwVPWooy?yQ0fsNd+`}?@v5~|v(o7<|-mxV|@anVE`cuj8xUc!{A'
    'H_Xk!ZS;^&A-osfHhXhg>X)qxFt*hVvp&6z-b+1?i|q<bLaP+@96E=vL4TQv<CC>%!4-VJ_MRaYr6Crj`PVmDZ={^Yf`aSDb0bN='
    'dGtHRUMe)lihq7o;GYP~x^BFrot~<E22<bOSFF|BYhG*~&Y%0n<R^F3pxOmUuD;52_@<qXT$cminEi&>xgO%>dWezhX*xYqXI)#0'
    '!b!cF)V`3ZSJOU3=(Z7_1}i6M<fjXt@~-LY&Z(dY8uwrhzBr!goGLd~t9xdmXL4$j>qp0F&**s=n$o=qeUIm2*9<+_|9w2Swo?;g'
    'Wjpt`C2Jq=AiY;3($e{8=?rE55-7(fl-&c(_kuEdpd244TL;S4ffzeNIXfY40Eim^;s$`Y0U&Mwh#LUn27tH$AZ`GN8vx=4fLH+_'
    'J^+Xt0AdAzu3OMG54z?-S!_`L8kEZhWwAjyWl(+@lxqg%ok2NhP(B)zn+9dBK{<3#<{Fe+2j#CpId>3O0hEIV<)A_LI4CC$%87%r'
    '<e=vOD0>ddT!ZrIpiDX_KMu;6gL3Gg96BiX4a$0hGT@-xHz@lL%J_pg0HEAAh|d6GIDi-qAkG6Q0}jfGgYx4bjs%E70pd=8coZN8'
    '1&BKV;!c3L6Cg$bh)V$C5`ee_AT9xjO90{$fLH_|MgfSY0pe_cGVh?wJ18#?%D;p1@}R5`h=~E>V1PInpqvpXBM-{agL3qstUV}y'
    '0m@~7@*1FA251%?l(h%VrGv8hplm*f=>cL{fEX7b_63Mp0peqTGHyb-HlbV_DAxwcwSjVNpj;a$*9OY9fpTr2TpNfP0^)>#*dU;c'
    '1}M7$%4>jlS)i;3C=UY4jDWHvLOBtkyopeL4V1qF<;6gGF%Zua#8U+^S3z7>5SJCiZUu2NL2OJAGZVzg1Tp16tT_;C6qEr0WkW!@'
    '3{Wlu#CHWTT|ul@5Z@KV;RNwWK@3t5_Z7s01#w?NJXjF-6~u!DF<?RY4iKvr#Ht0cLqY6N5Z4sMJ_WH)g;=;CUM`4D3gV!G_^2Qb'
    'Du|B?VxofbBcP0lP#zq_um!PgLCjbX3m3$91#w?NtY8pB7{nF^F^54cVi2Pk#7713Q9*eYP=*DR4FU14g?QIOylWvYw-EbUh_fxk'
    '-xgwS3$fXSINL&Ob|DtG5WiiB*Db_j7vio9@z_D!br6po#CsRwy@QzBAm%oRxea1&gP5)$p1cqT8?{p2a>G5FJ=uNJozK&{yIUvy'
    '<f&C*hBN>C+wRG0>x~Wm*eTJjr~7u$YEP$6S~(?G^>SCYn`4e{Snix?)!+TN@eI@Dt9ef0#({40yV=IO;Ea>KbckCo{Dv8H{DiZm'
    ';2rn9&gE_0<6bgg!n^MJ+ZFBjA;x*%e~6nCrgrIXcbxo~bhlG#U;Ab34QI{wBiyx*N7|O5&&wV&)*an?uHDzyN49nt<sO)}z(&6D'
    'x0Ajo-TippBAeB+TVmJW(%iw@=GoQjp7U%j80TiZx7c3lxFT`N?vZXv$_)G8`ZJ!rGsn2+x=**V=@ZWvWk$JCbw=3RGo#JTnWNoX'
    'x0>5GM-+HkxTD<kPs`cY8hq~Qu{^_l{FATEpE@h?(YoPocG}k_v*5MFsh^~|7eD>QxWhI$V^0ilBOh${9P58IG1Rxe`^AW0^Iz&H'
    'r_!gr+^l;^GIvs>Q>|HVH~sgio^MlQohhX{yAQfdG^d)L|EXYnS9j*p%C_b3c&GQ|-frQ*RJ-}eWXE09-7Ou`$ky!fsq@~A{;oT_'
    'tv&G16{lThKR2~oq#d*IvU9v(u=~cu;nvAG>^$y2+@0n7fsM%YI6(n}+%A`wm|%Cg^Ih8v_vW68wqBc5XHTyT_fBqWyZiY~PM7z`'
    'yA_snvw3UkJCkosa#t+Lvdvz}c8dCpcXwULuod@}@{Eg^=$5&;*xJDI&Z=G$-2dHOXuEr@NG#iFoO|u|WIO)&H7D%FNp3`+1-4<2'
    'Q1SAb;x1dT%=SGTBwlH$?t_0Om~TR7I|-dr-HxvxFjF2abIhS`ZnI^j?ef_f&ZN-p?vcXMc2l>F&XSBi?$Oi7P1PaW9AelCF>Hkx'
    'wn7YBA;zo_dse8H7pn1vYJZ{mUZELap;=#{d0?SBU8qhMs?CMweud_Kg=T$)d;p>OYN2{xXeL%@{#IyiS!hOAXhvFSj#OwyT4?@R'
    'Xf9f4URr3rTFBoJ@<W6?5Fu|wXf9f49$RQGTFCbh@<xQ_$%SUfh32b;cJ2u6*%8{&BeYvbXfKk`z9gZUe4$x=q5WJ!dwGQR><I1X'
    '5!$&Uw68~K$CJ>WFQHvvLOa5Q_J0ZO{}S5&CA9xbX#bbc{x6~ZUqbu8g!V}Z?UNGPIVH4<N@y+uG%o@2c0e;8pgub&Qv=G~;Qy#2'
    'o7n'
)

_PATH_B85 = (
    'c-j<~bwJf#ABWGjyPa)U5JUvTMi9XO6}!6;ySux)es*^tDh4WccXxMpcY}(6#QVH|JkRHQzUQ26ce?>XC_)Go8bb+9h>}oBYfMi8'
    '4Qr$W8jB{l3AF|~)=2}JFxM1HX~nf-S`jToE2I_Bg0#QtFEvj6p?*`psGn7bD%oLx#8Q~pBrT|>NKpecRTrwtSycr%Gh>Z?4pmcC'
    'RRN9T=>I>GT1Ba(R8Yz(Wt37%2_;M^s)Q<qm4ZsJl3&TE_$z)&ZY8IZUGY_X6feb7@lf2AjEalmR4hd*4rPN_C)SG9B3i5vQ6f?-'
    '5sSnEF;C19v&0NBO-vD!!~`*3j1{BBNHJUt6@$e<(O>ixy+u#aU33+lMMvQ+vWUzglW-HRB7?AbMHblD7EbIWGvExu1-p>0*i~f2'
    '8A&(nCfu<*nF(hS9@vA-j57;Q>`7+9S%eq%BE7M<@WDQ0R%lPRJ=qbr6|F@}(VVB!1e)PyWOLkHw7@OMmbj&8g<FxWacj{Aw;|i&'
    'wxS(wN4Cf9MF*~-1Lx?#sDnsR+@PIER9cC@N(+&oG!uUm2N=)<n$c^)Tr1YJfp)C#z?;oYq${o>P01iq6<Z{+K1ngbW}Jb(EAwuw'
    '%LJJrMM+ftDhbLT_)Gl{CsQZUNg|UO|D&IRlj$UrDM~s{qfVuhN~SSR$ElFcyihyvnmUS3xD(kKcNSf67qTnvD!SorWOv+M^uRsH'
    'p17yzg?o{`ac|KF_aXb@zM>!QNA}14#Q;2j9Eb;sL3j{37!MXh@DOq+9x8_6VdQW;T#UdY$dP!Y7==fXqw#1l29F`f;;~{J9!HMH'
    '<HdjYKXL+|ASU98<Rm;vOvaPRDR_#Qil>s(@H8<UPbX*K8Db`$NzTHv#B4m9oP+0xxp*!)56=_x@qBUtULY3Yh2$c<NG!&S$t8G+'
    'Sc;dDkvLK;!^_Ah93__H<>U&yLaf9q$!HucR^e6TYP?#k!E4C1c&&)RG2}YDPOQi4$qjgeh{dtwMsO$_sW*yEcoVr9RC*4+XwpQo'
    '_$c0sx9olcZ}EEZ8s6Yo@d{q!P3+nvw!lkxg}2bzBDUhK<TiK#FYz`y+r)Ofo!kMB;e~i8?u)zPs5mSRiv41**e!OlVh8NRJH;-%'
    'i`<QOi#>P`xfkyh`|v(;Ki)46-~;4Ad{7+1hseYDusDK`kVo-RaSR_LkHbm0i;vSeE>7SR<Vk!|oWiHb({NYZ!}q99!5MspJPY@j'
    'yN~aS2aF!jI|JwNIr2O_VD<s?5Aj3sh|VLbN7Rpbb&tsx_z^r|{Dk=@jGl<6jGpp}pHhFb&%$|*d0t$=7s!k7&3-DLvE~`~;u$M%'
    'F#cxWu%C(Nbe?lho^vOjGk3$jN%tmmx8R%oouhpxRp$-9ns3+&sLt>95Bfjsi=5%2xP&i}m&wcI5BoCX%i;>-E948tKRD7)P@O;7'
    '`_qoIAK4G=d-fg9a}#cJ*4y@TxJiAB{%yF6?~?cMJ^MbsPd>m8?1%Uv`3OI<ALGa56Ntl);VFJfK7%;U8pnC#*%8m0cxu(DIB)T)'
    'Zt<!Fwd&NUHRm1p3GwXs#kK!p|1Xa66rSVf<O}<XxXSCh$}7AEFX;W^9KY<}?D);-H*225OLn}ZdP)6?U9aqG?7Akd^X#wljIMK('
    '>vXQuy8*9Q`O1EcUz2ZG{l>n*><w{~ciK(fQ#aXplg>?gx9Hs>->~|P{T9C^-?8JJeTx;h#BJWKw^?<Y`W>_H?DzOR`GFN5?AziF'
    '@B2Hv+wZXQ4(mQJ`@#N*Ka!tV@rmk_{TY8Izt{)F7yA(0hCA>aKGXk7^_6G#l_&L;&R6>n)gPYJANKyC^T$qLl)$kQ=p@*G8U5wi'
    '{iROix)Pa5WRz$p;UqGd*ObgmGNWYsA9wQ~)j#SK>J;u%3M*3Rr188{IaVr}##|b`bk?SFq*O8;r$IVSXD)?fBy!$AT;~^F*9Y#&'
    '8}9iFp4~5=eLU|0h4+MmcZ9=v4<0}~XuMax*-!W^zTkW772k7j`2Ksxx9U5-3Exq_$M3}lIv=P$P=CZ9#V5XpKhgcf=o915kjU&`'
    '_9SqWKOE~fNBqTc<M}p-=W`#=S>hT0qW_!uKdeh&{a^MavOfuuaUz`rW`DCX9)43N&`V@4S^UHQ$P`G!{~#5ol4&?iq~ml_DCwXm'
    'sVE)(|A*yf@&7+A9aIWvj5TE|DAX!_UHK?<<ukA8v-raA&=-DvzVKSV(D_2|E4{Czt|UV$q=8_cLot+f!r(7UgIY3@im9v>CS8+}'
    '$=Je{V$-#$Y-%TVDj9GF(gnLHuGp2#h%+i~*o}0@?n)+{iS)o8N@kpy^u(S@7Mz9j!d{9u_9lI>kCGK<C4I54k_~4gv*YYa4xEF`'
    'iE}Esa4s@8&aLFZc}PF(r{u+XNq_9G1mFNNAI_%);y^M#&aVXFATk&SD+O=?vLG&~6vBnb!nm*!f<wqq9I6z-MaZJKs8S3UBg1f*'
    'QXCg2OW+bpNnDaFg-a==acQy)E~AviWyx~5oKhZ_CoA9zN=00etb{8mm2qXV3a+A5WmJ`_Ds?r`)oRq$l<Iu3R;Q{?T|=?>Z^a4K'
    'm0I*_a=e=Ct4UppUQ_0pDlVciG=Zk{nlV!oYI7yESznt`ZN_z=9yG&s=+sf_;<{u#Tu-Tw>yzQo1e)P+I^jwK+<=Tw+(iW0gsK5F'
    'R6ImOs)p2!m}|ti5u+Wji+Y#h30`6+?4q}u<LqYrZe^RYMcJgZQd)2Y&AHCzWDDFvX^C5st#B))HEvC|flatIw8d@7b`T32VH1v}'
    '(-zv}_GAax0I|3OoeoMzo^VI1j?|rCJ#4_8=yXy#^KR(Oiq4FtTScH4w1*i~Gpx4I9%fptm6?oY(x1!BT&p;gROY~3W@lL~m07Hr'
    'MLowVt;~iw)N>ilvSwRl=`@FyFpJ)7n9H%ITOB!fC#4IFg>|qVkEPQYx^jJ8sk%~kgR!_PbjRJv9xw*R;vRH*C_QmcvKNeoF}N3<'
    'UP^D=o9qLlU^MPSr;pMX_a*zmNEn6t(dno3$Nk9xFak#60dxi^1Mxs|5DbSAco3aI%3wU09HJ}{LzGAuqzqFQh+)biSOSAsJB<0k'
    'Fq9QTl_(fYJ;I6-Bdir-IE=7{DkH7IFw7ca4YCGU{j5G#FRQ!dt#r4tLN@5Zs0Y1XR6VUMN>9c;se3W%W%b6r$v(J`)fe|A`{908'
    'f83uOfCpFu@j!AA9%K#1gUKOyh&2=sC5Pc*)^IDD>l;cAvqr#3%=OY;L2hB~CU$S&=<7M(IxDlXj_X>-m8@gDp8f{TwShI8Si6NI'
    'ZDIFH_OG;714n`_n4Y!D%Al;WTwx`3w6&UgwdDrU)@InkQPy+h^&D}%6>DWuVmV_homj>jVG}c(sA6FgdscItHJoXU#s4^#t*qe;'
    'YdHEE`m34W2%9+WW@{_w*~$^O(%;Jdt;}tuzlGO1g4aEYdoqeUFp4_T8mKI_`YTJUzRDu2x3bXc3B9TN((BLMKqZo=8OiF=+}Y9W'
    '9ZkIyBJpTz40nGFGh?Wiz*0QM8cTO9xd@ivvDP@A**Lo6sK>(sScJ#Z8E^f^?0;1MQBQz*umDe>Gr^jOCz6w_KxL8@1QV<&<P@s_'
    'Okmv<<|e{qD?pjds>zHdTT#5%qNtYfURuUGXc=c&#<7;si(-Dcl~-BLj^&J&!E!5x9cv+mnHV~2d5^AT_gd!HGLEr!GrJ3RTe-*_'
    'kc&DG<b_?#$8em<T+0+|D%UsFDg;xw#`$<Yy=io&Ss~CBrqY|oYn=}Z@j`MDUd-%bt2^|Bsf?$=d|1f*67F*(&u=K7#bJCdNAMXR'
    '#dpIPzEfiGTIw})R?}a_Y&2`eDf7fQKGEaYF^+LG{Z-7bX5AXruVr5h``6*M%5-I_GFh3Z{HM$j<KaJLJp0G9b3DBX$}BN~?gZ+I'
    'j3z3R@Fa3Fo~%s4Q^=`!sxl2vBd6o($_zY%oC#~_u4dgTcCI2<GhRb~EnZD0n)5|-#%RtH&G<Tbowe5)U1z+Sb!)lab$tJB;P+!A'
    'zb~8dW^xPOqHM)m$!&O>vK?<HcffAE9d;@{BCGHbzOa+dPI|lWe){_v?^g~`9Uu?FbB^$w?sG;5;1E7U9){=23(od}6)zaQP+sDf'
    '%p8Iv_y~EF>pV)nWd0TPF*pt<cm*fOR~+FLv#*rbj9#<yHKW&zuiG1xH;mt~{|Fqz$Jl#Jc}n$!<KO36?vqa#Kc)YS*%NRQp5YU4'
    'ihFg6bDd&zit%YUtMn9S$s2GJp5YsGPqX5*at5Cv&*HPnIo6(|I!Aqjb+_;>@-{q$XZSXq+sYk$hrA0<;3>XK=dN-O-y`qC6MPRI'
    ';0NSG?)5`n$3sRBl}C&oDZV@(Uy%)GBeTOJB|CL?kpt%-bHXEbJW?Jr^H|AAH>b#jbCJ2BCOlSZQs;s^I1lLuHK3-bE~<*kqM|4-'
    '%8JsWq$n<mi6SCI6cPnQkO&k3A}>4qATQ1<{INe7fCEH6oR18|fg(T7PX^&25sZV$0=R%EhzpX1a3N6`7bZh+hzP}@WD#6M6vai!'
    'Vz`(H!(n7`TwIjECCHMvq$q_;k)?5IQ3jVG%i^-494<$e$K^!@T!E~JD~d|E5?L8n7FBQ+vMR1Bs`2`&(W%C$8sqA?I`_&Cs)<@;'
    'EoN(p+Elf9^|d)xZ926@9Y%Gy19f=abvR!gX6lH#Tt{6-b*URM(}?@f5E{{`#}(IOz8-Z$?nneQq;7=kiTb>{`mCr=9l;%H01?y;'
    'aeWcaT?*&kgmXv2Ss6~R0lfxf1P+G?);8k2wYlDETz_?*cMW*V`(?ZRK-p^Fg9p@)VXM8_t|~U#mBj$NqUdjzhl<pd#XuMY8=2n('
    'o9*hb$sS@4vIp7&?EWy2dN3YL4#7k0p?D}c3^vl;NN&QLIL{X9EzAss;dnSX!oH)7Ah)n$3v0IGt@bv$+qlkc%xq)La2RQK6(gxe'
    'Qjek@Wp{@W_D=hjvXk{Y>5jCcnTh7uQCvqPSGbhx9L=j5P0oX*^dh<9NamM86l+&NG)Io6in15k3+##ZfA%=Lv={?pVI0R8W0z%I'
    '9!A?^VH_R<<LvQvaWUR538i5id&k2Bx)Z1-P*21Y?MZkNIT_~DoySq;v3?%)e0mG;JXl~aWVDc6gcsS1?Ob9p)ne);b`G(G@e=A~'
    'tXRs9rR-Ts9SO_mN8w01kz|y;oX&FgEw(qXZv#i(z!gk_DRy2l#SVZ;)RXP0b{;X6-c;%hjHcMrn4M+^LNS<PPba7Ix~B6=rn750'
    'D`qf1!w!OJ_Dtqy(wS+`qBDzX7WHhpv#Dm=bL<c?hiVS>T<W=Y5hw<8?DcjbvDPjCg~WR1*0U~#aSXYRqphP}N4?%&OMfjHLqCR`'
    '!?9*_o@rdq6s~&%_iBS3%d3s$6~)qtWxSYsu$=p`0<W-F;+14Hj<#3Xoy98NIjb10vRB(##cDen<bWlNm%~a}Wv{Wl#Tw?<*d3uW'
    'tfse$V~phex6|HbpH+6*H{ceGV!WI8>2ABHIIr}EzG5z%SLQ1H#T=Nc%;s-{888daB4^{-${b}N^Rvj=tevCGV?0k846~@`Q_WX~'
    '!Yt|qR13%z{H?K^zdoY)dt{k1LoDO(mSy~<vW#&Q{pHNB;4CZHwSrv>*|$)c01K2wupCz4Ma(Qx7BjP0nFLc{p|X_KOO@d;7RJK_'
    'h@=y#jD*oJ7M8MhG5eRWZ;3Ju7IF4P95;&IVu<33qLh`)t>h|K(pgDoCB5aGe?G5o4zKw<zq{x8<vp)lV03}e1?3|5=OTCHBAttj'
    'FY#-AiJ41`E-9Cpy-anP`U=1NSD3xR=!$ZczniY|m(x|cSLs|;uJL!*HP&Ba<{F)A^scb)0_W?=^E#{S=IQO``R(L8W*gs1+xTAE'
    'Ztvh*aEDzJ9xFTezS==|2mMF<e&6T!{V9JF9OLhmH~bazhQDd9+p(|_Hp46a4tmbtRXh2cYX^Um?NRE(7T5-Rl@`znHo+FyqwG^^'
    'LtUs3EnqL~VQ)jFkrJUaRx*mliaSIoO&B#%nnE+&OsTHaP^u}q>QD{%tbS3y;;-a4{7wCizmq@k5A`ShNygzgH6F*4zwj^hH~vlj'
    'fxq}SB;W+{FaE10;zTkD@@sMM3;wD>S`z&vH5n(9{~$=quLWtr+7C6DmBEaH85h6>w1T)GSqK->3gg0L2oBLgaVS{?7txC1qGT~#'
    'ObgQ#5k?h8T^twJO3*1mRf4)Cl)@#TlvY}6EJ|xlp_EpEnF?ejx@G8<(V9bP#uc=R%vB^S;YwO%T$!xGY!%j)Wo22dC6r-Y8LHx{'
    'WHne$cR6dyv7(&T8p<**r<JEJueF8tP>x<T_EgiV<LYD$s0E8*xwe88E2vg5uEkt+sEKQmwQw!1Hm*(9fyKBs)Wvnldazhqf|pR&'
    'h5EQY84gRBTcNGw3@fQtGG0n|DY;UM#?jP~bRx-R+9GX?HcA_zwbfc{Ew$!aQ?0SqP;0=^!l40fphe&avLSA$HNuU^#<;Q81UDg@'
    ';-*?N+>C6Fn`<p_3$i6{skOqb$kw>E)&{pB+v2ubJKT<J55r*uZcnGZ)&X}QJHk*HjyuxnsCB}f$j;CehQLs*r`DZOXJ$HUU2qq&'
    'EAFaw!`;a4xVzQ^_aJ-Xo?0*5i|h?USTlr~A=E?hP;D61Fy?weAKZuR3&U_9=!g4}{b3mEhvVVAhLOC!k-VCb)T8hyZ8V+HRHLcK'
    ';4#`*?#NiGvDD*WAv5zi&ODgUzIhyL9!Hx;J)gM+u#k0&SUncT<MHHwu!!0Dtej6SghhA}&v+@%d>PMsnHEJiie40>D6N69K&x-`'
    'h5lTBe{BFBKn{euMk8pV4d#i~WxgKNH|E0vEgTvckq~awGwK=x*)>ob#M2%`HHdmJ^<c8DF_>|LF-U7@41hse8>1PtfC!@@G@{>#'
    'Y(v!$8XJAI#zsFF0F8_$(8g%Xj<!ZCXhhwPsvT83W*b9OqnFl{eN7oPW!wzf;ik~s=%F=dzB!}jj9WlEqdiAxZ?u7SMhECZw+mH!'
    '=t#e#(GGZ*(IJgaMk}L>){5QDp(V#`N!60N6>ep;X12A_4SGOJ#;w@Xfn#>%$X!|2l}=|?btbzq)0O#-&>43&x^b><MknAsN~asW'
    'PORy|wYBB-58`gt<zCl^a2#$lFa~hv`y1g}e<K1KL0x+FARHPP1C4sxK;{SXqz1Bb01U(fnTz7R5Y6|&Fufd<*9PnD#bCXY7ytud'
    '5Dcb21ct&eeWf;BkA|W85Pgsyr%lx+YZH0bjfV+%0yz;+)F$!WFo|!3NsJ~jo{T4JQ}7gWDxRuM<J)8!>!#72#oAe{ou$pDn$5Sz'
    'Y`!yQ^SPK!Zw@(!_xN0LE}x#cd{*W%p2Iokuxk#h=CE!O$C?6DwdoM2{m{N?U$jr!2ko8qMth~b(4J{ev`5+lZJ)Lu4!{Gd18@)?'
    'Xb<T;Bp=~N+GG5fe1e~7Pw`Xo8Gfcc$Ir<Z_=Wb8l`olpN%tk4m-JrYSK4c4UQ@lMeuLj=Z}D659e$_1$M4Ax_=ENle<VNQPugev'
    'nf!vkXkYPH@*Do9eaGL)ANYs%6aOURaGVye&E%J3CchLjU?z8C8qDDLVFuslGq~?F=**xu6VGJ*Pl(fgao2v){YCE=;{o~)t&09l'
    'tE_+0D(D}yGWt8M6qJTCjLSkfsK9(BsH}g1Z|wQO-Z*WLK0vRcSJo@)<@K_98NIY#QZKF-(~IaKdI3F1_tr0I7qoNQ8SRvILOZ4%'
    '(GKw}4#FXPNIQ%VlSl9o?I=D<9>d49<M=pv0-w-M;*;bld`dfwPm^cx8SN}SOP<5$wDb5pc>!P0F5-*iC45P{j4zW{z|t?kCCyvU'
    'qG#4K>2A8Ko<X;DQ#W*nuIfThbEG)_I@USXI#xTP9Z`-*#}dZ^$2`Xz$1KMT$27+oZK~s#HpOv7o9s9Mhu{d~WAsnJDLA7|b4+zi'
    'aZHA(?3s?IlQZxP$4oqvoP}pOX5-o996ZM{7tbZ<;dzevcs{uRFK{fx3&};W1TTcecrm#IFL5lzOUXza=~#xBkx@9xu^cZaS3opg'
    '4lD6WG8#uaRxw&dwTgN*UhP<e*N|)RT1O0yA=lw`j`eswxd9UB{$|%N&i0Gr|DyiQzTfl{nE%VF^$?3=$&K*W@rQN4;Sc`9y5I1J'
    'egY&@CGtuVIbtGf5*a5kP9l?;Pr*ralgNMgADMzv9H}^!Ov7o8bev8KJslLR@QhU|RoAdaI<Q06u}&J;&?T0niA~*NWKmhvHnw#q'
    'c9I!z2Hgd_kgnKO&xkXUZrDwC$L?e%oJse<9%N>mS@*=AWEPx7_rhMJH}=+jID-$z^<m`0I4kektn~62=d?V=1<<K`8fUbgbb1=o'
    '96g|?q38ids>9!y<H!sC#y@hN!w>QrN#p`p0!fVjF`w!PFw#NMdl)ku-Ju6{PeTJ8dKdwQzmeDQ1Apr7#w=FN0e|WM=DR~rBadNm'
    'jXruV!wD|nqw7u|-Eew>7wFDhMs8+u8yUeJav8eQa7w4UE}50oCbjAG08fxki?PL=<+Q16j$k`;gU;Au-eivt=k?Zoxj(-86+Y=#'
    'w5#|kc@2D-%cdXIvgyaQTYR5n({J%TauaT8H&}5MuH)<E4Sa*S({LSbu;!+AoAGVFUvAU8t=*xz!}rS_Mt8KkRCoD)xy$ITc8}^F'
    '=f212o_3$=K1aUK=sx4StiR3iZgCCXdJe8B2bl|ka1O507qasjvg_C22HXN)dfAxI$&Q?4E~;F5Zk(IU1A!2P^U%qo`(ZyaF9bj!'
    '&Pyk+?vMS+034v_!}-WS9H{5V`N<$0qzB_*vH&ii7sLh0LJ)!rLSbB(48b9KsQyd~)n7ni>JWYlLZK*~qEz{fCt5yZKOBSy@Ccr0'
    'fs6x<!*CRyX!(t2P?+_BMn1@I1ThmtCx}sy5zHu<QLs_K;CiSE&?^YVm?>uD)QcIpq2T}LjY7B(S=jK`3zNl+FlNK3!sr!(5N1NC'
    'La4)x;>;E|{J>uiHS$4z2r)v9B2-0;U?>O$7#D&N2xV<?b{A)VF|H$sYYydg7vcA?D1>nb!t_`028uE+#&2a9l)xp(lDMQ^3YQ{F'
    '<D$kJt*G%1*kP1_QuNF4TU!pw<MMh1T!E~JE9#YSC9*QE%x`m5>Z(*#sjKN-L^W~%RaK~ttCKZgfIg7ffmE-oF5)G;vT86}L$8Tz'
    'lC|K4)knOr`ibZ8g87$LH`exmUeE_>u>Ym?!m7odT6%3<o2;V`5Ov7s)&NnLx*j}d%?s<fRfiRI^t!mNUQZvyTy3&GReh@ZdN@@$'
    '*?>_4Mh)}`96>gOZk(YDSJ;Wy*@@TFiMk8DZmjOcd=FMdKqK6UYz#ecBWQw~kWHZntGlqfGk3Bx$LdVo1$WWA;;v*j+)eM!s5@16'
    '>K?d<-jm%uIYtv`hMSSip(kzzE%Xthg+2<JQ8(9HLQi(~)O+#i=*6fPqh5M%j@+B7H}wcUT_c$74<lGHLLW(IB-Kdvw}4h0v6Vgs'
    'TIi3g5#o{6glq<ntzqIZoyS%q{W0Cg))Q-xcw!BKVer^`W<}^v={>c=$q4-!E1$9IDLli^So6qg!8uy$tzo1-j<b*E+i5i41EZ<O'
    'P>&(U!Z=opqZ-4^7;>CG9*-ygW9C1q|MUrX0yz<~8!e$VM{ljS;T5#e$3ZLV)_Plh^V*Wxjkb*2>g{klvOO$dZUN_=4+|JC<kxZ`'
    'y@k|^SkVqT=o3W;st(j0sXOYEp*`~pVKH7zE`b$vSFomo{?HmH9$NpwL}<gf9duxB1uGZBQoNLm<aa%iU-L-n75Yk!y^>Wc8LiZ#'
    'aWuJ#?kcKP`f9wITm#<5WZ?zg#u|ES^tE^`83W!%40VjY4zDBEgSX*jOchzc%gAC(7oL#C@HA#p%@&!#)9^6djW{t^#EJQ^Q2c~A'
    'yjc8zpLnVG4nOcR@eRJ?<?vN}fp3g|ur5xx89zlv<A-oDzQYgdpY-B{yWwVJG+Yd)VHwiU4b4!DbUju7rytXg=!f(J`aXS+zKg$&'
    'cEB!uo4!Sl<@(pb2E2ic#j*NEyph}lTkuBMj5m{8@D_b5-b!x6+w|>tJGq0uvX;XR>Ros{>}0%?t_>L=l4ldCFXOo^<8P~F{6)2l'
    '&N4lUDvI|=6i+>hCm2OHihd+}c5<YhdTo2T{@Pjsk+58U3$^X-P}BZsy|><4udO%Czp<iWHN2+x2HxR!<a_+y`hY)>AMr=)6aGYg'
    'hH4zArd`FZWN+3h+8g!q_6FEUy;-khZ-ugUX}hHT-TKP<Pw)kQA;03U);Ii({Eoj{KkyIoClqH-2`Fiou>I`Zc1}CH?Q8qkA1ojH'
    'ljQ&(+hKp9Qf*<USt(Ysm1reczpZ%o|A06gN5<oL>lgk-{>HzpKll%sfD^30_%E4=6RjkiL?+{8>mU9{rr;DS6{nJEIL%7O>7=mJ'
    'LBR^wqEe~0hBeZG9k$Mu>h?GI0UBe2%CO@=qn1?C{so5Z&Q5o_?sQFhCh2Zx;^>)}$;2p=?SVa*wV1a^8$7TDPV6KzfCp<c+o@J&'
    'c4uasnNDWglgg9yvj17Gc9P{{|Ai##f0h@ky=+%@JHZ9Jkghl*=gMgRfxqBlyD@g-TyCs!W7dtHE64P-vvB+@?8-vzg}rQVM&8VN'
    'GxBDfnd@@rwd&j(A3H1eDJxZ0YG3SYXT#aZ>^Qrf1Lq)f;+%FaoQuqjbK7}v9?}o{*?DnZ(jSW3Kdmq*PF;eLKQsPz01hDYL6{wH'
    '6@_9D#<)10e9Y#v16dVF6-b>Q3PUIqgD@OQCqJ|K?I6w{#94#b5kx15UNF}i%vA<67tFXI?}`FYkh(AqW>qj96|zD$2&P{E3fU=E'
    'A>Pl0SYL>7VO-b_v6HP3W<nT+Fb>6`b`d+lDq<%>GK4S=wTs%nc})or%5@f{SCkCnwUyv=Sc*GUiu+NDQ7OiyacR2@ce4yLWf+xV'
    'To#wL%W=ocF;k9FImYFoB2>cV>6EuC*z5EPeBvuGs$kdWdDUl6eMa>ehudrQa8`sf3bz|D+kmP8b%ecIk6<=}QH0%yQ6u|})yRHl'
    'HH1cV8}d1C$h)B-yBacXgd4Fooa2_~{FUs=TxVsjrZROET*a=+>#0h&Dx<25tJ$CVeyYNET{Xtl?COlGQ&qQXP}Q)%!gnaixGGd<'
    'O-;L&{obm@w^}Xg+Kg)3b@&#oW52cPFjI$49eQ>7ZmY|g>vH_MtgK6~9=&>eyVhe=kMT~v%XjI!`Q_M6?!kNXy?8IV5AW0W<Nf3T'
    'd_X^l50Z!QA^k8uOdi2U^rQGFc?=)ZkK^Oy2}q{<gI(V_&Nq(ym0yytobN03H+tWh`@wO3ur3Lb+4B!4(fQ7bukfAvFaAUQi%uNB'
    'Q$P77`$@)eyf}KlnES(;zpPD!B%GlC*5g?f2k|(bRdEnc{}=qhf5-%!z|KFAz`nnb#5MfWQ@ENGG8L!lX*i8c$LYE-QXmb|b;S_;'
    'Hmg`AHLMv9>>zcl8;0TI@N#%MJRF~eha*+IRsMmZyj3)Kr)(APl<lBVzg6BVN#Z>#-ZOfyd|>8-vJ>7>zgIpgiQ*$GJ~H~Kd}8L4'
    'vKu~7e^fpzf5m53d}j1n`NGT>WiNc9{;Yge62w<ld}Z`i`NqsQWj}nO{;GUe{)q3a_|E9N@`ITl%0c)>{ayK~{1!i1@srU{C61Xm'
    '<uLr9{;9+(zeGGM;u%ph^Gi7jcOi~3bJV|;`w$Pm{tvx)_I~HwpSkw;y!KS#&i%;*9u8e`b2va(+`+?<$>HvBb4Vp4xH()M86395'
    'bQlhYLv;v8nwFv^Yl&Kd_FLNr58*ZZ!GFjEoS^;1f5}9gs3qYfG8rdp|L{LD1*d4KIF(GpX<9l?Cxs&&6s&Mgl}dGJSR)<S;n1;8'
    '8rX11EJ+ia4hvhPjctb$JIM?<gTn>8kgnL(k<nrCI$cOtUUNoADC1DZp^hR{MI26Wp)Sg<qEtnxi$Mf45e^r~sMLc75W!4Q2*Y7y'
    'afom<aMW|SD|<C}*6r0ils&Ll+pX=?wrg88MN3yx)qiR-q~H`X6{o6cIE_rl>8jAuAYD~7!5$T>qy}5)Zq`!OP1-+oqm~5!s8i{s'
    't6P}g%8Jd}CT*h@1e>V0(A&n$HukIF(0sVDzMxWTn$B1!x3O+J-mdLnw1d7wldO}hlbXpjm{cZpSIbxFYGqftKvzp@-7HhHxMGVn'
    '7As7~^ejuWwM70bN`@3j151<iP0O%^rGRS9Hx?N4jfL>XoNpvSGN{%9dJBw2pjwNl7a5E3VsZ(n>~*l$VI`T#<{xvR@sZg-W&%}$'
    '`H^)?U@3gWOCS<QlFQ&de8kJ>EHk2T6uBH$!aI16SJH`s6?g@?60bC(aWuIK-m&fj{y=`jAB|7=6Zshu%+J)HjW4YDLjMb+FO0uJ'
    '0@wVP`M+c`RRSb3PBg!==Bx1ye<Qy`qWPWryYU16Ab-MIdWq~wHj~VMW~><`17(2BEAz-)GM*JbAP&co@i^Z2g@2L1A(#A3{oDA1'
    '|BwlggI-R^C3DIgGJ$@A@fZIk6Cpdj95TC1q?2eQ;UqE{veC;fv&m#S$;LnYk4%9y$V%TAvPoa*B|W8wbe9>Wi*!m$N~udtDl*+j'
    'WlsvE;#BsfK&p|B(+wfhAl*=;V6DnXrBbOitVsuUkUG|-felh(DNSsW7UoZFY?Dsxlo@aa(gnLnSL{k=#2KX<b|c-fyUc_$ksjDX'
    'X2zLGPwXkP;4GvU_LAP%oAd!+><wAD;;d9zseSQwGtJlr+f8rkZKf)>ncK}BR6EF>baztiG<Wg!w#zhN2lY;Kx0zY)HnV^?>|(r!'
    '**&HSyUYiC4c@m@aL5PN4)eaX4R+AKZ#}Sfv39q)*UTjMa+JM{_L}?HxsQJ}_L&)A597V&e(L?EE4V=>*hg<Kdv|heS-Jjfya#gd'
    '9?2zh<J@E(oJaa$KQb@QEB$#o{yY<ZM*fTgaDdE*^O1o#Q0B+^$simggK;of0M?s<5F|H1tXY750a*|iBnv^Txxrj#t~G!1Ifysb'
    'z*=*SnM<xQ^T1j&hEWW;4zDxU<MreQyv58bx0nGC2r-PevS%yZt?b!KXDhw+tc^7{a^{U@A<kMz7M2;b-)aUeL3Kg~&B-^LlkYdD'
    'mO*o2#)T{_T{KrMUUg;cN;e}EW_Mxshe)Ru!ZAXqH*)NMd~Vap6s{|Uv!zg{bH+`aZ<86qo)B^)y(E6%(pjGjDLBPUWlt)f{Zzg&'
    'Qt70cX?z=`@p{vkNu!%aFNO8#>=l-7Z8mLfv+0BoxtVipHg)<2GY-Ci70~#O)vP6;P^<KH=A~uxeZ85Fj&51jM!wQF!DdJY2R)rN'
    '2H*7(T&Xf}+zcGUY2{X&WCnV!%yq*V=w`57telDqvo4G>k{K;OP^jIg+$?{{2N^AQy6#+!J2UQ9CaO$iBSsBb(a_2dZj3Wo9$dMH'
    '6$w$GG0tRVrp`=8KqDM()wAkYwX7OeH7m24Np(|Q)eNewmg8Ud3Q&o!mP(2V7TBt#nyR7dAk`|&>7+qVg2g^3c9I!z2Gs?-kgnKO'
    '&4@FSZrDwA$L?e%oJsY-9%N>mS@p!8WEQB(byc&fT3P61QN6Gi=?!`4Rkd<iIjn3}R?FMUVy!Sdd3~N_7R!^@>H(hgz36yZ(fm3^'
    '8>_*Ko;O`@%ZIKHl@E1RoYnHhzGOC>&B~6mlR0n>D<{rL=EAwG+&DLx$MWWyyj36ULuQ3M^s6$H8~m8}v$8UmRrSTbWH#`#vQcMK'
    'v*YY!4)9}#pOu%HyjBjnIn<muCz%WKGMm@(XU5;kMK_n48|NnTfWMW8I*;my{m8s<7S4gcbyhvCo>Y&kN7cjXL3O{nSKY1dRJW^J'
    ')y?Wgb%Q!i9ixs?N2tTpA?hHtvRY9sua;Fyt0mRqYB9Bl8lo0b3#dVApc=rD{lFjllL0tD&4=@mfjCgjkMom3I7kh~!DInkKrM(1'
    'l7(;~wJ<JBhTsr26o-;Ua1pgAE=m@|#ndnyMi$4#)e^V_SrV62OW{&vX<S+@gUgU*aapw-E=QKf<<$zf0$CAPR4d_1WMy1gt%9qN'
    'RiQcz!d2;1Rjc7@WOZC!t$}NhHDQoCn3aRcA$W*76b~hb;bH1<Je(YXN2nw5NOBY&rH;m<$uW40Iu?&5$Ki46cs!o`4>sWOFab{>'
    'Cvxv5lIysm>!>HgR9HuEJ#4`1STO-6;Ys9VJXxKBr;t;*-&48EQyEQFr%_F#nx;;tn$G>6PQ4Z`TT|3a)+F_!HCkQ5)h^*0SHneX'
    'ER2T<Fo`u&Si4$Xq%KhBsdLm>>I{xDgJ(5^Cp3fSGJ|8zP-jxj<hjhGo`q+rvl-2%noT_i&r#>%x#T=NPo0nFlMC<ybs=6zF2ak{'
    '#oXz|REw#Xz-qi0meOC!eP7DmUdmN3r5njJiliUO`bc#dPkb4jWz^9eGn#HRqbT}OWVE`9^RD39R&X^ds8_LS6*H@tU(UN{IV+b_'
    'uYgr}Ijm&;O5SHHnO{j~CB0P~E0Xgs<+@g@Yq<6`T<IF>i`=hEaM@bJy`B#9U;(V5w^ogz7sGvu;m*WxKVq1VVfM0h$+`%at!X^F'
    '$voS2Jns!^ERH2N;*IJiyoub5H>+Fl7IG`zs&2#E$nAK$x&!YZcjBGuF1(A}jd!bi@E&q6-mC7z`^f!xzj^>4AP?e$>LGlHJd6*k'
    'NAMByC_btl!^g<u__%rkpCC`-lj<paiad=^t7q^T@+>~f_f}pAfHQEO>O9{l=czByxj=P6y@)T8m*4}tKQQxw+RJ%~{w4J?zD!;L'
    'PkLFv%lSe5$W?sg+#lKVksV&nkC4Ub>Ab@FE9zD5=2fbz)Yrg+erE7=W_D(Bx;b5)8JtdV!7ijLc6DaN8A&(n=5)vIWG0-+>EXP_'
    '(XOf2Ir4R$&UHrb_yoV>`Msm}j`4e5-+OxRc~$SZ^7mZ9duHA<cb&aA*mr~U;D{a^Gc(T2HD_^pIlXxW-c;UBALk+UEl=kS&+92q'
    '@G;NyAy4@}&;2g%gqs}YCV2~P!(ICKnSaQ-$E<(KzBlZD%QJn;lk{;Ofn)HN{!`XGWc^+C-r_hnxUw7MEyj279r7-|tKP%+$ou%d'
    '`T##5AL57VBm9Vbj328{@DuVWeyTph&&cQShAZ&lmHF_x3OS$Cf3Ch@{sq+w>X#5eKOY1_K`6vsD8OAQKo*2T>@7^cu=5SP1s}$R'
    'm<x2~<N5hPUdZPRaK7ZIFV$CE&nwRIiqR{^uesXS^j=fvWKC}HhXAL)Gq*FR^EInpGn1Vso}Fjo>%66A<#}gy-hi8MOZ9c$0e5FM'
    'G8>tl%9rPt6@0NT<Lu5H%;s?3gKX5<Id%@nMJJc@0lbDBjB|3{JiOcTaK=2W%R?s*JwJMWWM1&cesujve_mTYUT=P0XMWzV`FWS-'
    'rxVOLnE7B<1hXcXUVhdEF(1TxH;B3b6vRQy1d*ZiLwWaw^4<&OK8Ml`rC*SHTG$!le5!_Uw?nwwA&k9wZ(iUtdzQaJa`U%KfOT38'
    ';IEMY{(1_a6JX`DPOACn=Hsuce01|!f!1*~kZvHIKr26ggXO2nPaR|(RfCufViaTr<6yFYbx<u}9fqS2%($SnmcR5?!5X}VT#MHl'
    'F*t@?2L)MKkhO)_U5KiXRhV6csR~nvKoM)dn#tU)x|uuG7`a_tBe$xn<Yx5~zsjHZuKmO}>?gigSJ7V$YgiK_cd~xB>JFLAy|7;`'
    '!WoKKnM`-{rMzqGFt!<6j7>(Yv7T#L2kY^AV*}nm#^P9GBi=}E!kdiEcr&>LZ!xywt>iYm&Df5&lRNMZV<+B8?t<HJ2kzoq#vXb*'
    'VK?4Q?!kMEy?8IV4{pLOypPU4V?W+c9)KHg6Ca>+z&MBxl84|r+`xzE95N2$!{iaT2G{WsI!BD7_$YY{uEI5ZjLtFRI6h9EfXi?N'
    'uHs9^1zyWJxPW)UZsQD`!+YTrJC4Iie3CqcPZ_82Y4Qv{W1MB>S+4dhqq9b1=YBW{r=f}SsL{lE98SV%XzXmtY*Xi9I0{V|H+G)o'
    'IOmM>9P>QYdFl)Jf^iXFBroAhT=_+~#C2abo^Ul!SpS3-Pv}3P_mo%ll>SpjPZ?j~HD2TX+~B_6;z{j-J#dR>bsO#)_jtnhc&_(&'
    'g7+BTXMCT0Dep7BZ#>}r@POU}>X-7ld@3KyZE}m;BxB`z86(%o)pC{mq>hwh)S+^OIsgXBVQLjQM6D#NLrwmQt*O?+waD5~kzOS^'
    '2!^PYp$hA(!9ey7hM{s4j8TWf2pB2H!6!8uR>_s}KRHg0k)vd5*-|!_O=V-*P&SbDWnEcY)|Ay{Rase9l(jiuZM6=rL)L`~^eV~<'
    'vM!yvYCUG^QPrca59R2WhYGU1EGtXPlCrogCOtHFEu-cNZrF`<$L?AtoQd?n9$IFcne@~$s-BuVcxXkXyH-SI)Iy~TWTbYd=b;so'
    'MP(5gDhonkD8jgy3}YrtdU6y`Eel7<LX}1H(p*$8MqZ4(G;hsRy)_G*-~wJ+R>;F_Zmu8~*OXKHsb<%{tG<w(ItS#`;=z?UH`Zig'
    'ZD#gl<#;}tq55!CAL^`(vTDBAm&^uvurFlCewst|W3`|5S&e~MO;tB&in>Zu1gL9Z1HD*H0|&%tU(~e_qpi_aX<@KhD-5Af6vAK?'
    'bE{!3Gi#~VQpezR>|3XOgM!qBVLhYu+7Ae(E(q&b7o%-p#|APM$8ueM+E@4vK3uae*Pczw0l6U$&Os*!cOnOOA_wDK)Vat!+{Y~3'
    '`@B58ykwZntNBy=YaZYUd9?rtlL7Ptw0!jPQRSl!qz=@)Ab|N|yl=vw1S?BWm7p$(OUhEX6j>UVmSu1mvMequ%i(fld7RBGC4J2R'
    '&DRX%_<>{z#--?&fpRj?Y`{CV9)#m?vH@<OM&JmtA>?CCAZzoRb=CZ4eP{rIW;W9ovYTFNcGCv}wd{1V)62m)2N_6}9da_xY5GDA'
    'GoRUzBR5nV;YMU*2%wjbxj<%fnz>k+iwrOuv!b!ugq2OGnou`|yz~Q@&&P^fW^PvJHnT%c$Yth%0Gu2AupgP%Y|8GYYBSu7Yz}$p'
    '2QcFY{>=NE&6#Viw!kgOmf+8<zggGmXV!u`&fI2gXHK;g)TXXOuddVI40kqH!<{YJ)lzMRTam4yBE4{DMQ3X|t<^TT4cQhdIxEqw'
    '<ZMf)t=bN^BilnIXK81cvxu{xTEtlxiaPVFMV-M=5Q;d9(Jkf-RXeMpWM{P~RhZfdI^z;*2j~c$aC?s0o=!Vx&$xqn*D3*})GKh;'
    'YNuYe+CV$%D^?l0SMgP=oZ4G0NA^}LsJ)=K+EeYWcIDo6;a$;%r_qJFEAFax!`;a4xVzc|_aJ-Xp6smzJ)kGY=%w~y+()ef)u0FT'
    'Wqn_&zSRBb_T!tqAESP1f4))s^N#G#s6XQY%nYD6fYCtu1G$ocoO>Wg7|5D|^arr659jI4wO_HW!F9Ncukp&RkvFUs>J6(Ew1I1k'
    'Z(7aNn{;nlU7<VNux>GPi<w*2Z92EDp3obvGQI{ktvgl|^$t7lu<H)v+pN98@$Xt4xX+z<7R7j0VLZJsXK|;$THKir@<UO^Va^it'
    'N|2?gibF}KpIVY$N$S$hGR%}AEAif`2K6D_S=U+1S%YyUXJy_um6@+hU6riDxQesAS^=uCvn=N>%R8kk$0^IWoU@Z!j`vDA>MD%N'
    'LV3pJSyP@-dBzo-9ogRr%CV*bREE+VzY^!H3e~x`>Rf3lXKp?Leo&HeX{ZX-xVGw0lWtAc)MQkXaV=cSS({F6s@l|ba2>L)vmW#H'
    'sOnMI=Lq!~*QXB0^&p(jR$e}%`S@PQ&-YJxes3$vN>CYBmQ|oCt}3hHYGid>UDm)g$eOsOtc7clwQ+4(2iGC%;<~aPu1D6#^<_8?'
    'CmY}fGJ;VARRncI+)y^cjmXBhv222ykWFz@*$g)$o8#uP1#UsM#4Tkj+=^_CTgx`M4cQht!6@98PFvXyw<Fs_2j~c$a0j~Wp#$!~'
    'xRdORJCj{tlpKvmQ+I~0xGUKWMl&}CkC9{XSaKX5C&%OQ<bU`-IYADSL*yXYNA{9E*w+=h<L+b++(Y)nJ;`3Um+XyulYMX>*%$XE'
    '`*F|vai{xH51<}E4#NGI?I-&))1N!vpHY7~nQAh3elmA>GWT>c-O2K_6#<Rp2{;9(t=?pBvM-#nPFPKtYX+_4aX4WevD(Rla0m{='
    '5$mvZ$m&Y319XJW(3Sav^bfQCD5IlRcQ{0S7>-!S7$38G!V&AZ)rMoYgCm^p81u)-<8YEQpR`&)D>%XRoMF!yuI~(M&d@nS@3b|U'
    '*Vm8NJ&=1akQ^ij<H6(*JVXw~L&;%ym>iCWlOtdPPh|p6WCG7*BIAj4hr>viNN)vCY&p+x8BcW?xt#F|`YZ8rxl}IZ-M5JM<3iq{'
    '3wY1Y<DEQ*_x5bw?X!6Q&*T#^jnBvwK1Eab3{BzFGllU~##6~@%+F-qEY{Cv-yHVOg?SunJ}lt43pxHG&a)UVq%)rtb67o#ozpnV'
    '6qqKb^S8%zKCRO^@^m`W>CND;lNt19P|sxjZ1&CN*mF6?JXpZ-7IEAq9DNC&oF&vt@lqMdD3VW4B%?^i%V0T<gedw^e1@X9CsA~w'
    '=q=}dtd!B*wP@~LG<PVP`!_*O;uA56&%q?_^CZUSts(N9)kU6#bJidjLT?yMqMk&av(8%GnC}7StPA7?s~7ZvL2#DdIqSSNf#XMW'
    '&Q*97|HG`2Yw=n#2FJ*CcpbSOua_I}1~L}M%8hs<xe0HQoAG9H3*I8P;;rO1yiIP$+sPg9SUx1T!%n=D+yxKieR)^zq239*@osVt'
    '-Xr(oz2rW)4R`TAI{V~)yq`P(H{muuK<9uwh!2v7;40jJoA|Q4D9_8Y^0YiDkISR-Fsly1VSHE~!AHoW_^3RFkCDgmad`rtAW!0x'
    '@)SNrp2nx;8GMF3i_gk)_#Am2pO+W#1@a=kC@(R(M0JV!GQKRY;49=+&V7}<fv><d&UcOK8ufMNu5&fl>0PIj)jTJCAgg(WyaZRM'
    'ugQka6S4s`be<zm!8sX0MmW#FIr`URBj+(V0S%p5O&>F>+0fa*837HQjhMgA`EGEpZsA+xZG2na!FR~J_^!N%?~(WMefa=CARpp~'
    '@)3SSKE{vb6a0jHil547_!;>eKbJ4?3-Tp?DPQ4N<ZEy<V`N5fGoMOVa|>*fF5qfDCU?jT;9@=`cS$E?Fz=Il;4a)}>@+hl@4|Xl'
    'j*$`E%;)e@x|?ohM$;9%ID;2Q_hRH_dNcAi*F!99f-T_1IyckZ%w&3C4>B_pu`*L<Ha$6>Cw)&wo{Y1Yca1Fce!*|^zVX|9U_3Np'
    'VG}$s;u-%o<IRW0BV#?p!b9T-<DU?3zUB_RmT&MI@-6(N7YFg?PxFZR$ark5ff!g1kBmd~j+lqc$5aQ*cg6wp3mi088VAi)@D2_z'
    'e-IASIc%<h$8eDGA&z;J9Y<Mnl+jVf$KWSE3dfl{ZhnKK)W^&d@Y9Sl-*SC#<vTv5@Az!KWAu*kd&cj{Q_RP)GLH4f;iUPI&;Lh0'
    '?H}MH-U;v7^OxO!`3(Q%760WZe`O-0L_WKT)Ta3g5@izOBtD}_ykC--F-^;SCX?wT^I1*iJ(bLiWxjw{kO)ci{xSQH_uoHO{F5n+'
    'Qus8dP^a=9O=TvPQL0R%n?{vJoz8nXo!N9o=~9?!kS-PT4%`D_DyE86QZsK!jTw!RW;)E%(qW#3^Pn=;Or2UcFM?*;q-|b?8*mGB'
    '))?kVX|U7am<GEHQ<_JmG>^kcNCQF7V6DzEG|rpOb^hb^CGk2<^Dp=DJ@@mY{KR+eC+_qo>XYUt`I&Fz&-6aiImwea$+I|RzUTRT'
    'fRAv3XLO4GX`b<EcAPdp%P;Ku!k*LYIBlL`<_z64<`?;u@B6RJer5g}^*8d2d6pGt%^z^ae8;MH<~LS+li&HR_|B^D)bChzjy31V'
    'x9|?1GtbjGZ^pqn^8&nqxA+1x7tD*yTr_{ddFl)1C3p$1;SGLC=OSEY&1LfsBpDT<3(SMd%wA^x3cSRZ;VS*BR9C65!3(pG*~{!<'
    'b~6*?4}R%>aLqrs;ve!Szk)yM{G?96ar`pJ@jDsEuVfr^arFK`g8a>|{V({9m%?%x55HIu&z^Yl7yiZkAL>6;f2b31g6v}cmYvN-'
    'vXi+`b~NY9GUi-a%A6xhnzLn?ISXb}&!IP0mWDE{DQBh{WuY8(M{@xzWd9<LvlxDJ%mmpLx|v<gE@nmZpHTrSn&sJ3-YjR9F-x1J'
    '%#vnNGt|r{L(Tj$2tpv#3^9YuV8#U@6pBDF4mOKI5c9!i0qO!~F$iWHY8Ltb3c3a96*P-O0mdN^$~lTaF*?PlicyC_Nn8wyn=@r$'
    'v!pD<u0mvCvouVD8T{QfgPbXga~F!6g*bX4voI9L#o1llEWuGr&@Vx^1f3G}!Z>y*USAorteMVTDovK*HJ3FjF|K4PvXbc!r5U%U'
    's%&bYgTHKS=9Z1joU);rLq?d{WgVzz`a(9yPA>;@Ia!mNwSG|9tis+ZWMi|D+0cwI>zK978fG>6Rhg-3N~prPDpbeS$r`wZSrgYJ'
    'YvEdEZCsnIgX@@eab2<=u4mRaJ!O5<3w)t2<8V6RRN-a=_BCL214a!Pw=+FtThm>(g4U*sY-u`WbFQMfX@Qfm3;m4X&N>g-jw7{W'
    'XB&>wf-7pyH8v+(Fm6M?9d1FVh1n9fBwIlnvn_5*-4a^k)?{1y?QlD;qdwPNhx^fx`_kBK!X0YDeQ3g~Z^CPCLbr+8l&UGOxhbof'
    '(rIcoW7Ld&&DhzDZZmpK*zYgf^G<EglWotFYj1X7)PZ+b2i{8^c;X$H=|H~{&$%4$^9sDvE07hbDw>_CI@0e*c7o3Iy5LT9I+0!Y'
    'oOCn0<L+b++{5gNdy>6yFS9r9P4>Zk%)YoU*$<w>3%*BQ;%j`XTr;oZ>*NjQ`$B)*pBw-;=szcK!E@>t_y((Qm^blF@)qm*!$3Tc'
    '90a$Rxn<tQx5+#3jP5h$2Et%Gm>dF6;TbD#!(DTcxxk#qtD9%e$Mbo8^LbVC887%>#pMCt)4Bg~obU7aJ*TRz+KRSrmr=AxB0+*A'
    'A~i~5g@`1G$WUTMWC=nBU4Q@n%{!~Agv3gX5JV&?Y9tY|WfG&k?Hz6Jeg9uC@6UHW>zv;?InYlXpP`>&KSw`ze1U#}{U5l+47Zr$'
    'wj<uL-m%uPn%Sda6}k$$8eQ#JgRa4@Mb|oF&=~AGSdYd)EE<blkFIybp>f!FG~SVbCSVicHfxnr*~Z-4m~k6(Y$GnGRs!Wj<@DU6'
    'eh>d1{(ZEZk+<Lud%nZYzknU+4($KJ9jcG1wQ|Zwy!jvUSK^`L7r5$pNc@Ov@rYV0J&(D*t=zju(8}FtC4S6xc#QW59y8Y+)+%Ag'
    '36O*)VK+btl@doOUMX=BB%{gLjZlgv!zOeSb~BW+yHfVJ1HMGR#Qq<YGE=FejE*w;HbDy4JcTQrLX<+hh5NmQ+!p*YMwB`3;@u@q'
    'acre;E7yE0y;~irM5)}BR5Gc=Y1lOOkVZAlkxrCOl<vsD%V575L>Z3TCI(_54iX><GU!WVjuh6}#SV7z``n4$MSPcC+-3J)!cKH2'
    'b{E`5cRF_SwCv^?*v*LDRChb}@HFiqyN76xV=uqLz5Mp}a^LoHCH9itOMV}})qQmCqrQ*KK61O6Zx{2Hag9p27v=m0?(;lc<2kD2'
    '8LZ|Rt>%fWCaNZ`L2LL{sN;L1p0AR6M=R9fH}GsXP-!4)Aa0`4<ai7Xjz(&Y%+$!}M#eYN*GRs}(aigynQAjpGjR(eTKG%bLcWDe'
    '3%PpM%Hz8!m+z{ld@Db5{K(h)kJz8^e&YWHUHN~)Q2zh$o*7~W!%%c6_C0ij`I8=I_P{>)lOApcnD<Q&=mqb<05jYSg7?iZ^24yh'
    '(c$!tV4e}o;bCrS4|5ATJ3LHR{$J7+JJgJ&>O`ND`HQaBf6+DIWNLJ!F3|V&K{y2YP@pS_E3lQi5Gu%3V5{_gH~<Hs0xFs5Z?GRK'
    'nX#H&HMW*<wPb4Xomkfy++i&0%r2ab3oE;rT3ttHoi2i6s3lhiPSl;vNK>pwn(v_woQ*5KtGNcwW;D2?u5`J8t8t^^h8>MJ3V)Qj'
    '4sOJwU<^72>yEl}jmCgG`|&X2=o@Elz)cuMJO(_d4dtG^YX+MB=56zqdDFaM{$To<*Ufn2X}nCQc3!44cp7gaZ!-a%fb~Ir%tUk|'
    ')))0PAD|y#C!v$fWOOoi3OdD1MW<pvL_ajs&}rC@Oeg3JQ@{_;&vb!FFa>51%`jcT7bd|>qM4>U_<%3WBAR7-f;afUY@*rb73c$='
    ';0<$#=9pJuJb1!vdS^1HA8UVTrn4h|^G;iTGXSRI&&8W-27$i`WdDI=1Mx4|{^p`R*UY0f&kTmS#24&9vw$-%pmPCz=ZP=a=j{b1'
    'i0cwWC5Zfa`tr!;VK1T=?Muvb$)0Bdm?^*vg?Yqz<O|3a*a2of+4<&u7!CpC^6Y%(xXj#_?I07(T?l54U{=T?zHDdN!6t-z7sA~N'
    'p&CLh%g!d7ZHGXXeHzZdW%M+aW8{xvPvaf8Uu<{W?gSy`IPnR)L%S1pM|csA(R0Q=Yv<UmZBIdteUkb~x{kw1`;<M3yxr~;*;B+h'
    'WOD59Y^S#0*)HG;IgI}fPQw}d9JO=A=kPCcu6)jS1q#r7GWpm7`zrObb}sAZvQ92D=Q2+&bL5ggNBs&E*oF4+wuM}^LVG@3B`zXU'
    '#2Q6(6_F`sonriA<}POTVn!B|FQT`A>wb~@JB{DNOXdahoO#}KFdfm3W})fZb|KzE{Ke=ZSd1<<?JcpCrL8V)wbc!JfU*u--@+j)'
    '6V0@akU2un5uzi+N718J7Gtu=W)Wo(XQSEH2XfT%l}u|ixXVE}1exTHQp>g`$p_*qZZcAwWrPd|C)5e+j5>=8>Vh4Kjucna73+q&'
    '$tZLbb~N~+qhJg=2J4QxiwEj~9V_2hV_AJH(O4OWj>C?Z1J-yd<B7(LC+dmyk|CCtd<_S{lh_;e#!jFzLEZyzd>=d?83x|?!Duix'
    '1QwEAC?g<5f+SD^WUl<%nk&CqbHE?wioeW}|5&qOj?9*}G7Dy-mdt=z;wSCF$VcFZJ_ql^aPXr?L3{9%ndD}2m1a_zNj!_}EWBCF'
    'H-~lR$~<%)HUJHf`RIIXAQ~tO&;{5aG>8){fFSlAEQ`1vi#YirPPT~rB3aCJTTFH_(PD|_+OFVgFXt|N%zatL9+qK0CSFc{1@&k~'
    'M6=!scCeh?e9WGfvA1RHZW;c^<d#!gK~FS0iDu?#qUBVU!E*d))>_1VLb$H!dW5wFQXyS0lnfmLYxQcqQm@cn)(SlVqS0ub3eT(`'
    't!LO3)T3b)nN@hJ@K>X&^%`^yb}hPA$DlFTb&y6jg^`<?cat6q<H5_?OfH4-Db&;G%b+_3V$oRaddQ%X!pKdKqPL=3@V8*M5~rbC'
    'AQj!lNw#Ts7z>+-w~*gTPb#FN>DUZ3LvLs1?aUtwak|lp)6Eczzh1|~b~FwWbc8ICU#unaPb(CbNGQL*P<{cS-1kswVe)q?jE*q;'
    'aB|^f!|@}iER`B-sno&WA&gu&MB+tKi^NaRkrG8ml+?pg{77<ftQ)Trb+{z5ej@&M_I${M$hRgCf*?c=neF7hHHXY$6R!`OL`Eg)'
    'dMk<ZBr$K2j)FM7fwOJU4<Qym882D4!W#S-h=q-0HtHwv3|0}Zfn@sQm@|RB9A>q{tajLBngGdUADJc`5_KloO!9|J2EQX8o@Xza'
    '$n!l>_QTg;oBoz<2Ew~A1op#3`o{C_aOWN4%e!lmOhG5}PMXYHXfnCU#8b#mMJK~l`B0|IFc=}zU^=;JywRpHW*QySh^Nyv9dA0l'
    '@5xYkL0*)Xq?5cXozc$NE@&6&igv|zL%T_Lv^%y3+CzGxJ+Zw&>t6W1<Q4Q4Y;Vw-e_HAGXnXBI9aw`JZKF2!IrKT*0quZ&9(`VS'
    ')Q{S9)UD6~f4uG@<6u0|INeRg!Z`ZJ>K^!7d$6*H?#-&br4QN%+ZRTX^I!)fbzgFQ<yCQj4Sk@myaq1RM(TFjS+~)>^cmGlpHpYm'
    'IhBj%V$VY_{VTN5PSl+AdGhDg1@r<o51e!!exACBUc_DkC;FY4*G0d^TCd6LqQL>L%G>PWZRr4g;2peoq$9j71K9llvIB_vlk3kt'
    '>Cav1Pdq>d;tj+bNIZ~u5b+?c_8>+LA~Q(d<$k<N=3V^3R0ne>2NMmJA$UW$lS8<FL+Bbpb_n@F%=0#TdYwJ?V~_o?F6?_G*UbZU'
    ';S^3>87HiZcI7m#c&^%wGrQ?aocEHtj9$j(gBzW0bhyzoiux#>Pc2_vL9bv7RGh?0jI5DW^0T#4j=@jxv$aZAl3R_pTK)m6=vfVG'
    '(Y4qZG)C5;>#(tCtgM$eq#cO-0p370^y4)Buy4ql(gxbW8}zP&Scya9B%XRa*?6L4Y%)D>$*<O1@;kJ_e^Zj=UsfV}NyH{mOCq-c'
    'l9_1(`$%MGiP#Oq$!H=Y-hxE@BuHlNc-Bf_HwmnlfS=6{ve<tXHk-IW9hFQuBnRby?3b_LYxHaE0rY@;gMNcOh#r)0(QmPb&_i+<'
    'J&esnGvx?+1bY-c%KS&*C~F*Ljcoj5T*G6me2mI5IW8xx<FXNZ7>>X(ImaD1$8|qP=Q-kB?oKX!x#V;Ie+0cJu;&?fUN*sII3Xw5'
    '$4P1@@lVMXI6?jb)eA)5!38oG$e)B9&XB{19HJcJ?<5s+;53!fc&G8ta23vA^Qh)YI-DVYM$VEy%QZPm?^!Zu$>qsKIxfmK_yo?t'
    'CHX6S1!v%*T&8jv@3Q1m$;ZpbzXG*XYUMMyLhgzb$RFX)kPlbnD%3!&R7<7YmvSkS61gom<%aBlFJY$?!!@{p7Rz2KgktoMP{14o'
    '@{Bp3vGz0OeMVeJwor=DB5W~QEZ?KwW3Qpt<T`pCdjq{8KcGKgZ=yHl7SS!dTllxp+j0lJgDpWzq!ca1mZ4>G7rl!uN6Y0NdJlUa'
    'y)PAL1-25clq&X9g;#}NjaGB^t579%*gE!ChyQ?%2Y3&po=iRatS71`Zh#hMY@wqC{~?)rXr!l+JvS0H5;w8GChSAH9?B#3_lQxC'
    'h#nEQ61P%qC2Ez&^foiLnG-hSKc;%z+=YAa2ujH{KofH}(bEV`#I4Nrfc@5Rj#{)<o^Yq1$QMuzPw}2|_NScoDVe8o%#=&ExhYv@'
    '2i$<0#J8aY%AlN{`|wmwm@i-lWSML@fgXbs=n3jiSno2wy*z%$r}+J!=h?~S$>O=<dCcay%;){+s@-|3y6b*28r*qny1{6jz`G-X'
    'T)rAj>`rEkj*~Iu$B-MN3wWOvsH?nJui{<BFI1UQ$or&_s8AKDLsCShh^R>2gZt{Bl&b@9Q0`N`Pp+A2G4JnU<|)Q+rt_{URd>`a'
    'm91{VE%dnh0dArv)eZPTUFYxPb^ZokgX`!8^*vleFG4X~BY#8Xz-c%O*BN&MZZhX>)eZzS9EEJS#k#klglY+134SSBs>;wZ>|OM('
    'Do4w)_t1Nst6Wv6{Zhf%D)1|*R+6byRqA)CBB~;)Qq@G&stvXslt39&sT#)CP^+P<M%AjnNiCUL^$Yw8ze5dumCSvg^_tj613P=b'
    'N$NOf9Ve^fTy?|`IKu;K4fHgz!zTKh(FU@0P|uaAXG}d&J#hotpc=VijZ_+m8i||GCdRdJM_Q=05Vw$NAy>q`E#Ur-<~QNW-{g_}'
    'oz{E{Il$)or~}_i9krK!*v5;mC@-RMRK{UF^~>VPca$f-7m=6t*3E6a>GY=JO~#vCN4~#a&@bwjbSJ&7O(*>nUeYfUy{tQv>5SJI'
    'zYE$$ch%i=cilt(S@qC=h3<O3-3@x^p2R)%SMUUS=m2u_?RmDp{j&DAXWKJvKl>l*Bk;37vj2(qFYvQx*gvZoWM|;dB${c@LT6!T'
    'qqFTf=p3v+>Tl0Q=VIrf^Xve-C+p0`&a>yE;r0_1Za;&bI-EF?T7><RieQZhW{qI32xf>NA4zv4UZfqxh$y<E$V8EeA{W4Xfp%9N'
    '$ms%EFOU@i?FF1=f!zhVg1;SPzodi61+l*%JJ^0v2a^dV3bsS+7jy`j5d1})W)ay%WEa}c>4o<5@B)O8TZ}FyzZgG^s}M$a7*VKg'
    'w6Fe6`G7Cq(G&Tyo}mAuCg`?U3lzEb^cWq=tf98A_Mz@W#fQoS@S!>pLYY65IhWYKsU`F+!4D$}g)n<5_hPC2Z}<&9BKCtN5XPQ@'
    'Ih#Lc59FG3*L&4&wM%`j0#t9kK_#gTDj7}2ZiL>tj}B0MsPxer$!=7e&`sFQ&_{2^->g#56zmrGM6FlbU^{$5+(-9ihQ4(6)t}Ij'
    '0$b6o*i_gKpP;E^QdJtWr!iX^9cg6J$fd(}Gz~IT0;EAYtHeP9q*LEU?iHN?NstU_kU@Ss^M49`^{3EB_tuFjUd5=jYN=YMhCsNA'
    'P|h$CT)_=SLkNVcNHqeSAzVeNVK4&185cz^0;1G1^&Sj^DDul-sR~m|)KoQDO;R5yUsYi$O_ixOo@%-JSglaeuo7LVR;ksn23@0;'
    '>Ue9Z{v5u9J+MZFlMC00utr7dl_~;1LT`YLu#(&=2-iy?0wU2UYEgPKJcSi1ioPiFk<78%+GXvu##tVgi`Ayhe*t1*h|~'
)


def decode_cow():
    v_data = zlib.decompress(base64.b85decode(_VERTICES_B85.encode("ascii")))
    p_data = zlib.decompress(base64.b85decode(_PATH_B85.encode("ascii")))

    vertices = np.frombuffer(v_data, dtype="<f4").reshape(VERTEX_COUNT, 3).copy()
    path = np.frombuffer(p_data, dtype="<u2").astype(np.int32)

    if len(path) != PATH_COUNT:
        raise RuntimeError("Błąd danych zaszytego modelu krowy.")

    return vertices, path


# ============================================================
# MACIERZE OBROTU
# ============================================================

def rotation_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, c,   -s ],
        [0.0, s,    c ],
    ], dtype=np.float32)


def rotation_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([
        [ c,  0.0, s],
        [0.0, 1.0, 0.0],
        [-s,  0.0, c],
    ], dtype=np.float32)


def rotation_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([
        [c, -s,  0.0],
        [s,  c,  0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)


# ============================================================
# RENDER JEDNEJ KLATKI
# ============================================================

def render_frame(vertices, path, angle):
    rx = rotation_x(np.deg2rad(TILT_X_DEG))
    ry = rotation_y(angle)
    rz = rotation_z(np.deg2rad(TILT_Z_DEG))

    p = vertices @ rx.T
    p = p @ ry.T
    p = p @ rz.T

    x = p[:, 0]
    y = p[:, 1]
    z = p[:, 2]

    # projekcja perspektywiczna
    perspective = CAMERA_DISTANCE / (CAMERA_DISTANCE - z)
    x = x * perspective
    y = y * perspective

    x = x[path]
    y = y[path]

    if FLIP_X:
        x = -x
    if FLIP_Y:
        y = -y

    return x.astype(np.float32), y.astype(np.float32)


# ============================================================
# CAŁA ANIMACJA
# ============================================================

def generate_cow_animation():
    vertices, path = decode_cow()

    frames = int(round(ROTATION_PERIOD * ANIMATION_FPS))
    samples_per_trace = len(path)
    total_traces = frames * TRACE_REPEATS
    total_samples = samples_per_trace * total_traces

    # SDG6052X ma limit 20 Mpts przebiegu ARB.
    if total_samples > 20_000_000:
        raise ValueError(
            f"Za dużo próbek: {total_samples:,}. "
            "Zmniejsz ROTATION_PERIOD, ANIMATION_FPS lub TRACE_REPEATS."
        )

    X = np.empty(total_samples, dtype=np.float32)
    Y = np.empty(total_samples, dtype=np.float32)

    cursor = 0

    for frame in range(frames):
        angle = (
            ROTATION_DIRECTION
            * 2.0 * np.pi
            * frame / frames
        )

        x, y = render_frame(vertices, path, angle)

        for _ in range(TRACE_REPEATS):
            n = len(x)
            X[cursor:cursor+n] = x
            Y[cursor:cursor+n] = y
            cursor += n

    # Wspólna normalizacja X/Y — zachowuje proporcje modelu.
    # Wspólna normalizacja X/Y
    maximum = max(float(np.max(np.abs(X))), float(np.max(np.abs(Y))))

    X_STRETCH = 1.2   # lekko szerzej
    Y_STRETCH = 1.00   # bez zmian

    X *= SCREEN_FILL * X_STRETCH / maximum
    Y *= SCREEN_FILL * Y_STRETCH / maximum

    # Cała tablica odpowiada dokładnie jednemu pełnemu obrotowi.
    sample_rate = len(X) / ROTATION_PERIOD

    print()
    print("==============================")
    print("KROWA 3D")
    print("==============================")
    print(f"wierzchołków modelu : {len(vertices)}")
    print(f"punktów ścieżki     : {len(path)}")
    print(f"klatek              : {frames}")
    print(f"rysowań / s         : {ANIMATION_FPS * TRACE_REPEATS} Hz")
    print(f"próbek / kanał      : {len(X):,}")
    print(f"sample rate         : {sample_rate:,.0f} Sa/s")
    print(f"pełny obrót         : {ROTATION_PERIOD:.2f} s")

    return X, Y, sample_rate


# ============================================================
# 16-bit TrueArb SDG6000X
# ============================================================

def waveform_to_bytes(waveform):
    waveform = np.clip(waveform, -1.0, 1.0)
    # 16-bit signed two's-complement, little endian
    return np.round(waveform * 32767.0).astype("<i2").tobytes()


def find_siglent(rm):
    resources = rm.list_resources()

    print()
    print("Urządzenia VISA:")
    for r in resources:
        print(" ", r)

    for resource in resources:
        inst = None
        try:
            inst = rm.open_resource(resource)
            inst.timeout = 2000
            inst.read_termination = "\n"
            inst.write_termination = "\n"
            idn = inst.query("*IDN?").strip()
            print(f"{resource} -> {idn}")

            if "SIGLENT" in idn.upper() and "SDG" in idn.upper():
                return resource
        except Exception:
            pass
        finally:
            if inst is not None:
                try:
                    inst.close()
                except Exception:
                    pass

    raise RuntimeError("Nie znaleziono generatora SIGLENT SDG.")


def upload_waveform(inst, channel, name, waveform):
    data = waveform_to_bytes(waveform)

    print()
    print(f"Wysyłanie {name} -> CH{channel}")
    print(f"  {len(waveform):,} próbek")
    print(f"  {len(data) / 1024 / 1024:.2f} MiB")

    # FREQ ma znaczenie pomocnicze; ostateczny czas odtwarzania
    # ustawia niżej SampleRATE w trybie TARB.
    nominal_frequency = 1.0 / ROTATION_PERIOD

    header = (
        f"C{channel}:WVDT "
        f"WVNM,{name},"
        f"FREQ,{nominal_frequency},"
        f"TYPE,8,"
        f"AMPL,{VPP},"
        f"OFST,{OFFSET},"
        f"PHASE,0,"
        f"WAVEDATA,"
    ).encode("ascii")

    # write_raw nie wykonuje konwersji binarnych danych przebiegu.
    inst.write_raw(header + data)
    time.sleep(1.0)

    inst.write(f"C{channel}:ARWV NAME,{name}")
    time.sleep(0.2)
    inst.write(f"C{channel}:BSWV WVTP,ARB")
    inst.write(f"C{channel}:BSWV AMP,{VPP}")
    inst.write(f"C{channel}:BSWV OFST,{OFFSET}")


# ============================================================
# MAIN
# ============================================================

def main():
    X, Y, sample_rate = generate_cow_animation()

    rm = pyvisa.ResourceManager()
    resource = VISA_RESOURCE or find_siglent(rm)

    print()
    print("Łączenie z:")
    print(resource)

    inst = rm.open_resource(resource)
    inst.timeout = 180_000
    inst.chunk_size = 32 * 1024 * 1024
    inst.read_termination = "\n"
    inst.write_termination = "\n"

    try:
        print(inst.query("*IDN?").strip())

        inst.write("OUT_BOTHCH OFF")
        inst.write("C1:OUTP LOAD,HZ")
        inst.write("C2:OUTP LOAD,HZ")

        upload_waveform(inst, 1, "COW3D_X", X)
        upload_waveform(inst, 2, "COW3D_Y", Y)

        # TrueArb: każdy punkt jest odtwarzany w zadanym tempie,
        # LINE interpoluje odcinki pomiędzy kolejnymi wierzchołkami.
        inst.write(f"C1:SRATE MODE,TARB,VALUE,{sample_rate:.6f},INTER,LINE")
        inst.write(f"C2:SRATE MODE,TARB,VALUE,{sample_rate:.6f},INTER,LINE")

        time.sleep(0.5)
        inst.write("EQPHASE")
        time.sleep(0.2)
        inst.write("OUT_BOTHCH ON")
        time.sleep(0.2)
        inst.write("EQPHASE")

        print()
        print("==============================")
        print("KROWA URUCHOMIONA")
        print("==============================")
        print("SDG CH1 -> HM303-6 CH I  (X)")
        print("SDG CH2 -> HM303-6 CH II (Y)")
        print(f"Vpp       : {VPP:.2f} V")
        print(f"SampleRate: {sample_rate:,.0f} Sa/s")

    finally:
        inst.close()
        rm.close()


if __name__ == "__main__":
    main()
