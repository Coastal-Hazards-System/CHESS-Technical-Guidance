# CEM Conversion — Corpus-wide Equation Audit

_Every numbered (tagged) display equation re-read from its precise source crop with a local vision-LLM (qwen2.5-VL) and compared to the published Markdown at the symbol level. Generated 2026-06-25._

> **Resolved since this audit:** the three real errors below were corrected (III-3-21 reverted from a wrong `= 1` to the source's sign-cases form; II-7-33 `F_{c,fric}` duplicate → `F_{c,form}`; II-1-62 `C_\sigma` → `C_g`), and a systematic glyph class the audit surfaced in the review list was cleared by a deterministic remediation pass: `\mathsf{p}` → `\rho` (density) and `\mathfrak{n}` → `\eta` (e.g. II-1-82/96/121/145). The remaining review items below still stand.

## Summary

- Tagged display equations audited: **1167**
- Symbol-level **match**: **1030**
- **DIFFERS** (flagged for review): **137**
- Equation not locatable in the Markdown: 2

The audit re-reads only the numbered equations that carry a `\tag` (the others have no stable key to match a Markdown line). A single vision-LLM read is noisy, so DIFFERS is a review queue, not an auto-merge: each flag is confirmed against the source crop before any edit.

## DIFFERS by category

| Category | Count | Meaning |
| --- | --: | --- |
| Real errors fixed | 3 | Confirmed against source and corrected (III-3-21, II-7-33, II-1-62). |
| Source-erratum corrections | 3 | Earlier fixes that correct an error in the *original manual* (diverge from faithful reproduction); pending a faithfulness decision. |
| Glyph fixes (kept) | 8 | The Markdown diverges from the raw source glyph because a remediation pass corrected source-font corruption (ρ→p, α→∞, ε̇→&, tanh). Correct; kept. |
| Multi-equation crop | 12 | The source crop bounding box caught an adjacent equation, so the source reading has extra content. False positive. |
| Text-label markup | 26 | Descriptive words in the equation are not wrapped in `\text{}`, so they render as run-together italics; the source uses `\text{}`. A formatting cleanup, not a content error. |
| Needs review | 85 | Smaller symbol differences to be checked individually against the crop. |

## Real errors fixed  (3)

| Tag | Chapter | dist | Markdown | Source reading |
| --- | --- | --: | --- | --- |
| III-3-21 | part-03/ch-03 | 16 | `\Delta y' + \left(\frac{1}{A'}\right)^{\frac{3}{2}} = 1` | `\Delta y' + \left(\frac{1}{A'}\right)^{\frac{3}{2}} - 1 \begin{cases} < 0, & \text{intersecting profiles} \\ > 0, & \text{non-intersecting profiles} \end{cases}` |
| II-7-33 | part-02/ch-07 | 15 | `F_{c,tot} = F_{c,fric} + F_{c,fric} + F_{c,prop}` | `F_{c,\text{tot}} = F_{c,\text{form}} + F_{c,\text{fric}} + F_{c,\text{prop}}` |
| II-1-62 | part-02/ch-01 | 2 | `\bar{P} = \bar{E}C_{\sigma} = \bar{E}C` | `\overline{P} = \overline{E}_{C_g} = \overline{E}_C (\text{shallow water})` |

## Source-erratum corrections (faithfulness decision pending)  (3)

| Tag | Chapter | dist | Markdown | Source reading |
| --- | --- | --: | --- | --- |
| II-1-148 | part-02/ch-01 | 7 | `m_i = \int_0^\infty f^i E(f) df` | `m_i = \int_0^\infty f^i \ E(t) \ df \quad i = 0,1,2,\ldots` |
| II-1-133 | part-02/ch-01 | 6 | `H_{\max} = \left[ \sqrt{\ln N} + \frac{0.2886}{\sqrt{\ln N}} - \frac{0.247}{(\ln N)^{3/2}} \right] H_{rms}` | `H_{\max} = \left[ \sqrt{\log N} + \frac{0.2886}{\sqrt{\log N}} - \frac{0.247}{(\log N)^{3/2}} \right] H_{rms}` |
| II-3-3 | part-02/ch-03 | 3 | `\Omega (x,y,t) = k(x\cos\theta + y\sin\theta) - \omega t` | `\Omega(x,y,t) = (k\cos\theta + k\sin\theta - \omega t)` |

## Text-label markup (wrap descriptive words in \text{})  (26)

| Tag | Chapter | dist | Markdown | Source reading |
| --- | --- | --: | --- | --- |
| VI-5-241 | part-06/ch-05 | 81 | `F = \frac{moment \ of \ shear \ strength \ along \ failure \ circle}{moment \ of \ weight \ of \ failure \ mass \ and \ surface \ loads}` | `F = \frac{\text{moment of shear strength along failure circle}}{\text{moment of weight of failure mass and surface loads}}` |
| VI-5-240 | part-06/ch-05 | 55 | `F = \frac{available shear strength}{shear strength required for stability}` | `F = \frac{\text{available shear strength}}{\text{shear strength required for stability}}` |
| VI-5-239 | part-06/ch-05 | 46 | `F = \frac{M_s}{M_D} = \frac{moment\ of\ stabilizing\ forces}{moment\ of\ driving\ forces}` | `F = \frac{M_s}{M_D} = \frac{\text{moment of stabilizing forces}}{\text{moment of driving forces}}` |
| VI-5-13 | part-06/ch-05 | 45 | `R_{ui} \%/H_s = A \xi_{om} \qquad \text{for } 1.0 < \xi_{om} \le 1.5` | `\[ R_{ui} \% / H_S = \begin{cases} A \xi_{om} & \text{for } 1.0 < \xi_{om} \leq 1.5 \\ B (\xi_{om})^C & \text{for } 1.5 < \xi_{om} \leq (D/B)^{1/C} \\ D & \text` |
| V-6-24 | part-05/ch-06 | 36 | `R e p o r t e d V a l u e = B e s t E s t i m a t e \pm U n c e r t a i n t y` | `\text{Reported Value} = \text{Best Estimate} \pm \text{Uncertainty}` |
| II-6-18 | part-02/ch-06 | 34 | `R = \frac{A_{avg}}{Average \ Wetted \ Perimeter} \approx \frac{A_{avg}}{Average \ Width}` | `R = \frac{A_{avg}}{\text{Average Wetted Perimeter}} \approx \frac{A_{avg}}{\text{Average Width}}` |
| VI-5-206 | part-06/ch-05 | 29 | `G_{\text{max}} = \begin{cases} \frac{6908 (2.17 - e)^{2}}{1 + e} \sqrt{p'} & round - grained \\ \frac{3230 (2.97 - e)^{2}}{1 + e} \sqrt{p'} & angular - grained ` | `G_{\max} = \begin{cases} \dfrac{6908(2.17-e)^2}{1+e}\sqrt{p'} & \text{round-grained} \\ \dfrac{3230(2.97-e)^2}{1+e}\sqrt{p'} & \text{angular-grained} \end{cases` |
| VI-6-37 | part-06/ch-06 | 26 | `\sigma' = \frac{\sigma}{\mu} = \frac{standard\ deviation}{mean\ value}` | `\sigma' = \frac{\sigma}{\mu} = \frac{\text{standard deviation}}{\text{mean value}}` |
| VI-6-63 | part-06/ch-06 | 26 | `G = G(\gamma_H \hat{H}_S^T, \hat{\rho}_c, \hat{U}_{Hor.Force}, \hat{U}_{Ver.Force}, \hat{U}_{Hor.Moment}, \hat{U}_{Ver.Moment}, \\ \hat{\zeta}, \frac{1}{\gamma_` | `G = G(\gamma_H\hat{H}_S^T,\hat{\rho}_c,\hat{U}_{Hor.\text{Force}},\hat{U}_{Ver.\text{Force}},\hat{U}_{Hor.\text{Moment}},\hat{U}_{Ver.\text{Moment}},\hat{\zeta}` |
| VI-5-213 | part-06/ch-05 | 25 | `\varphi_{m'ax} - \varphi_{c'rit} = 0.8 \, \psi_{max} = \begin{cases} 5^{\circ} \, I_r & plane \, strain \\ 3^{\circ} \, I_r & triaxial \, strain \end{cases}` | `\varphi_{m'ax} - \varphi_{c'rit} = 0.8 \psi_{max} = \begin{cases} 5^\circ I_r & \text{plane strain} \\ 3^\circ I_r & \text{triaxial strain} \end{cases}` |
| III-1-15 | part-03/ch-01 | 20 | `S a t u r a t e d \, B u l k \, D e n s i t y \, = \, ( N \, \rho _ { s } ) \, + \, ( P \, \rho )` | `\text{Saturated Bulk Density} = (N \rho_s) + (P \rho)` |
| VI-4-7 | part-06/ch-04 | 18 | `PR = \frac{D_{85} of \ protected \ soil}{EOS}` | `PR = \frac{D_{85} \text{ of protected soil}}{\text{EOS}}` |
| VI-6-38 | part-06/ch-06 | 16 | `X_i^{design} = \gamma_i^{\text{load}} \cdot X_{i,ch}^{\text{load}}, \quad X_i^{design} = \frac{X_{i,ch}^{\text{res}}}{\gamma_i^{\text{res}}}` | `X_i^{\text{design}} = \gamma_i^{\text{load}} \cdot X_{i,\text{ch}}^{\text{load}}, \quad X_i^{\text{design}} = \frac{X_{i,\text{ch}}^{\text{res}}}{\gamma_i}` |
| VI-5-49 | part-06/ch-05 | 11 | `C _ { r i } = \frac { 0 . 8 2 \xi _ { \sigma } ^ { 2 } } { 2 2 . 8 5 + \xi _ { \sigma } ^ { 2 } } \mathrm { \, f o r \, r u b b l e \mathrm { - } m o u n d \ s ` | `C_{ri} = \frac{0.82\xi_\sigma^2}{22.85 + \xi_\sigma^2} \text{ for rubble-mound slopes}` |
| V-4-15 | part-05/ch-04 | 10 | `t_p = \frac{-m - \sqrt{m^2 - 4\ln}}{2l}` | `t_p = \frac{-m - \sqrt{m^2 - 4ln}}{2l} \quad \text{for } \sqrt{\epsilon t}/a < 1.0` |
| V-6-23 | part-05/ch-06 | 10 | `\sum Q_{source} - \sum Q_{sink} - \Delta V + P - R = \text{Residual}` | `\sum Q_{\text{source}} - \sum Q_{\text{sink}} - \Delta V + P - R = \text{Residual}` |
| VI-6-31 | part-06/ch-06 | 9 | `P_f(T \ years) = 1 - [1 - P_f \ (1 \ year)]^T` | `P_f(T\text{ years}) = 1 - [1 - P_f(1\text{ year})]^T` |
| II-7-34 | part-02/ch-07 | 8 | `F_{c,form} = -\frac{1}{2} \rho_w C_{c,form} B T V_c^2 \cos \theta_c` | `F_{c,\text{form}} = -\frac{1}{2} \rho_w C_{c,\text{form}} B T V_c^2 \cos{\theta_c}` |
| II-7-35 | part-02/ch-07 | 8 | `F_{c,fric} = -\frac{1}{2} \rho_w C_{c,fric} S V_c^2 \cos \theta_c` | `F_{c,\text{fric}} = -\frac{1}{2} \rho_w C_{c,\text{fric}} S V_c^2 \cos\theta_c` |
| II-7-36 | part-02/ch-07 | 8 | `C_{c,friction} = \frac{0.075}{(\log_{10} R_n - 2)^2}` | `C_{c,\text{friction}} = \frac{0.075}{(\log_{10} R_n - 2)^2}` |
| II-7-39 | part-02/ch-07 | 8 | `F_{c,prop} = -\frac{1}{2} \rho_w C_{c,prop} A_p V_c^2 \cos \theta_c` | `F_{c,\text{prop}} = -\frac{1}{2} \rho_w C_{c,\text{prop}} A_p V_c^2 \cos\theta_c` |
| II-4-40 | part-02/ch-04 | 7 | `V _ { m i d } \, = \, 1 . 1 7 \, \sqrt { g \, H _ { r m s , b } } \, \sin { \, \alpha _ { b } } \, \cos { \, \alpha _ { b } }` | `V_{\text{mid}} = 1.17 \sqrt{g H_{\text{rms,b}}} \sin \alpha_b \cos \alpha_b` |
| III-4-9 | part-03/ch-04 | 7 | `\frac{U_{sea}}{U_{land}} = \left[ \frac{H_{sea} C_{D, land}}{H_{land} C_{D, sea}} \right]^{\frac{1}{2}}` | `\frac{U_{sea}}{U_{land}} = \left[\frac{H_{sea} C_{D,\text{land}}}{H_{land} C_{D,\text{sea}}}\right]^{\frac{1}{2}}` |
| II-1-159 | part-02/ch-01 | 6 | `\Phi(\omega, d) = \frac{\left[k^{-3} \frac{\partial k}{\partial \omega}\right]_{d=finite}}{\left[k^{-3} \frac{\partial k}{\partial \omega}\right]_{d=\infty}} s` | `\Phi(\omega,d) = \frac{\left[k^{-3}\frac{\partial k}{\partial\omega}\right]_{d=\text{finite}} s}{\left[k^{-3}\frac{\partial k}{\partial\omega}\right]_{d=\infty}` |
| II-4-15 | part-02/ch-04 | 6 | `H_{stable} = \Gamma d` | `H_{\text{stable}} = \Gamma d` |
| III-6-90 | part-03/ch-06 | 6 | `u_{c} = \frac{u_{*c}}{\kappa} \frac{u_{*c}}{u_{*m}} \frac{\ln \frac{\delta_{cw}}{z_{0}}}{\ln \frac{\delta_{cw}}{z_{r}}} \ln \frac{z}{z_{r}} \quad \text{for} \qu` | `u_{c} = \frac{u_{*c}}{\kappa}\left(\frac{u_{*c}}{u_{*m}}\right)\ln\frac{\delta_{cw}}{z_{0}}\ln\frac{z}{z_{r}} \quad \text{for} \quad z < \delta_{cw}` |

## Needs review  (85)

| Tag | Chapter | dist | Markdown | Source reading |
| --- | --- | --: | --- | --- |
| VI-5-222 | part-06/ch-05 | 38 | `I_{x} = \frac{1}{\rho_{w} g} \frac{d_{p}}{dx}` | `I_x = -\frac{\pi H_s}{L'} e^{-\delta \frac{2\pi}{L'} x} \left[ \delta \cos \left( \frac{2\pi}{L'} x + \frac{2\pi}{T_p} t \right) + \sin \left( \frac{2\pi}{L'} x` |
| V-6-53 | part-05/ch-06 | 31 | `\Delta V_N = \Delta V_G - D_L - D_R - D_O - S_U = (1 - j_i - p_1 + j_1 - j_1 m_1)` | `\Delta V_N = \Delta V_G - D_L - D_R - D_O - S_U = (1-j_i-p_1+,_{1}-j_1m_1)R_1-(1-j_2-p_2+m_2-j_2m_2)L_2-D_L-D_R-D_O-S_U` |
| II-1-139 | part-02/ch-01 | 30 | `p(H,T) = \frac{\pi f(v)}{4} \left(\frac{H_*}{T_*}\right)^2 \exp\left\{-\frac{\pi H^2}{4} \left[1 + \frac{1 - \sqrt{1 + v^2}}{v^2}\right]\right\}` | `p(H,T) = \frac{\pi f(v)}{4} \left(\frac{H_*}{T_*}\right)^2 \exp\left\{-\frac{\pi H^2}{4} \left[1 + \frac{1 - \sqrt{1 + v^2}}{v^2}\right]\right\} \] where \[ H_*` |
| V-3-6 | part-05/ch-03 | 21 | `\frac { L _ { s } } { Y } \, = \, 1 . 5 \, { \ t o \ 2 }` | `\(\frac{L_s}{Y} = 1.5\) to \(2\) single breakwater (V-3-6)` |
| II-5-19 | part-02/ch-05 | 11 | `H(t)_{local} = H_0 + \sum_{n=1}^{N} f_n H_n \cos \left[ a_n t + \text{Greenwich } V_0 + u \right) - pL + \frac{a_n S}{15} - \kappa_n` | `H(t)_{local} = H_0 + \sum_{n=1}^{N} f_n H_n \cos[a_nt + Greenwich\ V_0 + u) - pL + \frac{\alpha_n S}{15} - \kappa_n]` |
| II-1-114 | part-02/ch-01 | 10 | `P(H > H_d) = \frac{m}{N}` | `P(H > H_d) = \frac{m}{N} \quad P(H \leq H_d) = 1 - \frac{m}{N}` |
| II-1-127 | part-02/ch-01 | 10 | `p(x) = \frac{1}{\sqrt{2\pi}} e^{\left(-\frac{x^2}{2}\right)}` | `p(x) = \frac{1}{\sqrt{2\pi}} e^{-\frac{x^2}{2}}, \quad \Phi(x) = \int_0^x p(y) \, dy` |
| VI-6-33 | part-06/ch-06 | 10 | `U p p e r b o u n d \, p _ { f s } ^ { U } = 1 - ( 1 - P _ { f 1 } ) \ ( 1 - P _ { f 2 } ) \ldots ( 1 - P _ { f n } )` | `P_{f_s}^U = 1 - (1-P_{f_1})(1-P_{f_2})\ldots(1-P_{f_n})` |
| V-6-62b | part-05/ch-06 | 9 | `S_{\text{LEFT}} = \Delta V_G - S_U - S_{\text{RIGHT}} = (1 - j_1 - p_1 + m_1 - j_1 m_1) R_1` | `S_{LEFT} = \Delta V_G - S_U - S_{RIGHT} = (1-j_1-p_1+m_1-j_1\ m_1) R_1` |
| VI-5-150 | part-06/ch-05 | 9 | `p_3 = \alpha_3 p_1` | `p_3 = \alpha_3 p_1 - (VI-5-150)` |
| II-1-116 | part-02/ch-01 | 7 | `T_{z} = \frac{T_{r}}{N_{z}}` | `T_{z} = \frac{T_{r}}{N_{z}}, \quad T_{c} = \frac{T_{r}}{N_{c}}` |
| II-1-36 | part-02/ch-01 | 5 | `A = B = \frac{H}{2} e^{\left(\frac{2\pi z}{L}\right)}` | `A = B = \frac{H}{2} e^{\left(\frac{2\pi z}{L}\right)} \text{ for } \frac{d}{L} > \frac{1}{2} (\text{i.e., deepwater limit})` |
| II-5-17 | part-02/ch-05 | 5 | `(t_0) = local(t_0) + \frac{S}{15}` | `\text{Greenwich}\left(t_{0}\right) = \text{local}\left(t_{0}\right) + \frac{S}{15}` |
| III-6-41 | part-03/ch-06 | 5 | `\bar { \bar { F } } _ { D , g r a i n } \propto \tau _ { b } \: D ^ { 2 }` | `\overline{\widetilde{F}}_{D,\text{grain}} \propto \tau_b D^2` |
| III-6-42 | part-03/ch-06 | 5 | `W_{grain} \propto (\rho_s - \rho)gD^3` | `W_{\text{grain}} \propto (\rho_s - \rho) g D^3` |
| VI-5-115 | part-06/ch-05 | 5 | `D_{sieve} \approx 1.15 \left(\frac{W}{w_a}\right)^{1/3}` | `D_{\text{sieve}} \approx 1.15 \left( \frac{W}{w_a} \right)^{\!1/3}` |
| VI-5-185 | part-06/ch-05 | 5 | `F_{surge} \approx 0.18\rho g H_b^2 \left( 1 - \frac{X_1 \tan \beta}{R_a} \right)^2` | `F_{\text{surge}} \approx 0.18\rho gH_b^2\left(1-\frac{X_1\tan\beta}{R_a}\right)^2` |
| VI-5-204 | part-06/ch-05 | 5 | `\sigma_v = z \gamma` | `\sigma_v = z \gamma,\text{ based on total stress} \\ \sigma'_v = z \gamma',\text{ based on effective stress}` |
| II-1-100 | part-02/ch-01 | 4 | `\Psi(x,-d) = 0` | `\Psi(x,-d) = 0 \quad \text{at } z = -d` |
| II-1-136 | part-02/ch-01 | 4 | `\tau \ = \ \frac { T \ - \ T _ { 0 , 1 } } { \upsilon T _ { 0 , 1 } } \quad \ ; \quad \nu \ = \ \frac { m _ { 0 } m _ { 2 } \ - \ m _ { 1 } ^ { 2 } } { m _ { 1 ` | `\tau = \frac{T - T_{0,1}}{\mathfrak{v}T_{0,1}} \quad ; \quad \mathfrak{v} = \frac{m_0 m_2 - m_1^2}{m_1^2}` |
| II-1-141 | part-02/ch-01 | 4 | `T_*^{\max} = \frac{2\sqrt{1+v^2}}{1+\sqrt{1+\frac{16v^2}{\pi H_*^2}}}` | `T_{*}^{\max } = \frac{2\sqrt{1+\nu^{2}}}{1 + \sqrt{1+ \frac{16\nu^{2}}{\pi H_{*}^{2}}}}` |
| II-2-20 | part-02/ch-02 | 4 | `R _ { m a x } = A ^ { \frac { 1 } { B } }` | `R_{\max} = A^{\frac{1}{B}}` |
| II-6-21 | part-02/ch-06 | 4 | `\frac{\Delta}{a_o} = 1 - \frac{\left(\frac{a_b}{a_o}\right)^2}{4\left(\frac{d}{a_o}\right)} - \frac{a_o}{mW} \left[\frac{1}{2} - \left(\frac{a_b}{a_o}\right)\co` | `\frac{\Delta}{a_o} = 1 - \left(\frac{a_b}{a_o}\right)^2 - \frac{a_o}{mW}\left[\frac{1}{2} - \left(\frac{a_b}{a_o}\right)\cos\epsilon - \frac{3}{2}\left(\frac{a_` |
| II-6-23 | part-02/ch-06 | 4 | `K_{\text{inlet 1}} + K_{\text{inlet 2}} + \dots K_{\text{inlet n}} = K_{\text{all inlets}}` | `K_{\text{inlet } 1} + K_{\text{inlet } 2} + \ldots + K_{\text{inlet } n} = K_{\text{all inlets}}` |
| II-6-25 | part-02/ch-06 | 4 | `Q_{\text{max}} = Q_{1\text{max}} + Q_{2\text{max}} + Q_{3\text{max}} + \dots` | `Q_{\max} = Q_{1\max} + Q_{2\max} + Q_{3\max} + \ldots` |
| III-2-33 | part-03/ch-02 | 4 | `y = \frac{Y_o}{2} \left\{ (1-X) \ erf (U(1-X)) + (1+X) \ erf (U (1+X)) -2 \ Xerf (UX) + \frac{1}{\sqrt{\pi}U} \left( e^{-U^2 (1+X)^2} + e^{-U^2 (1-X)^2} - 2e^{-` | `y = \frac{Y_o}{2} \left\{ (1-X) \operatorname{erf}(U(1-X)) + (1+X) \operatorname{erf}(U(1+X)) - 2 X \operatorname{erf}(UX) \right. \\ \left. + \frac{1}{\sqrt{\p` |
| III-3-1 | part-03/ch-03 | 4 | `\overline{\tau_b} = \rho \frac{f}{8} \overline{\|\nu_b\| \nu_b}` | `\overline{\tau}_{b} = \rho \frac{f}{8} \frac{\left\|v_{b}\right\| v_{b}}{}` |
| III-4-14 | part-03/ch-04 | 4 | `R_T = 1 - 0.06878 \|T_a - T_s\|^{0.3811} sign(T_a - T_s)` | `R_T = 1 - 0.06878 \|T_a - T_s\|^{0.3811} \text{sign}(T_a - T_s)` |
| III-6-48 | part-03/ch-06 | 4 | `\psi_{cr} = 0.1 \text{Re}_{*}^{-1/3} \quad \text{for} \quad \text{Re}_{*} < 1` | `\Psi_{cr} = 0.1 \mathrm{Re}_{*}^{-1/3} \quad \text{for} \quad \mathrm{Re}_{*} < 1` |
| III-6-92 | part-03/ch-06 | 4 | `I_{3} = \frac{\ln \frac{\delta_{cw}}{z_{0}}}{\ln \frac{\delta_{cw}}{z_{r}}} \frac{\kappa u_{*c}}{\kappa u_{*m} - w_{f}} \left\{ \ln \frac{\delta_{cw}}{z_{r}} - ` | `I_3 = \frac{\ln \frac{\delta_{cw}}{z_r} - \frac{\kappa u_{*m}-w_f}{\kappa u_{*c}} \left\{ \ln \frac{\delta_{cw}}{z_r} - \frac{\kappa u_{*m}-w_f}{\kappa u_{*m}-w` |
| V-3-1 | part-05/ch-03 | 4 | `(BCR)_{F} = \frac{\text{Storm damage reduction benefits}}{\text{Total, life-cycle cost}}` | `(\text{BCR})_{\text{F}} = \frac{\text{Storm damage reduction benefits}}{\text{Total, life-cycle cost}}` |
| VI-5-246 | part-06/ch-05 | 4 | `F = \frac { R \displaystyle \sum _ { i = 1 } ^ { n } \Bigl [ c _ { 1 } , b _ { i } + \left( W _ { i } - u _ { p i } b _ { i } \right) \tan \varphi _ { i } ^ { }` | `F = \frac{\sum_{i=1}^{n}\left[c_{1'}b_i + (W_i - u_{pi'}b_i)\tan\varphi_{i'}\right]/\left[(1+\tan\alpha_i\tan\varphi_{i'}/F)\cos\alpha_i\right]}{M_D + R\sum_{i=` |
| VI-6-5 | part-06/ch-06 | 4 | `P_f = \operatorname{Prob}(g \le 0)` | `P_f = \text{Prob}\left(g \leq 0\right)` |
| VI-6-21 | part-06/ch-06 | 4 | `\beta_{HL} = \min_{g(\bar{z})=0} \left( \sum_{i=1}^{n} z_i^2 \right)^{1/2}` | `\beta_{HL} = \min_{g(\bar{z})=0}\left( \sqrt[n]{\sum_{i=1}^{n} z_i^2} \right)` |
| VI-6-43 | part-06/ch-06 | 4 | `G = \frac{1}{\gamma_Z} \hat{\Delta} \hat{D}_n (K_D \ c\hat{o}t \ \alpha)^{1/3} - \gamma_H \hat{H}_S^T` | `G = \frac{1}{\gamma_Z} \Delta \hat{D}_n (K_D \cot \alpha)^{1/3} - \gamma_H \hat{H}_S^T` |
| II-1-156 | part-02/ch-01 | 3 | `E(\omega) = \frac{1}{4} \sum_{j=1}^{2} \frac{\left(\frac{4\lambda_{j} + 1}{4}\omega_{0j}^{4}\right)^{\lambda_{j}}}{\Gamma(\lambda_{j})} \frac{H_{sj}^{2}}{\omega` | `E(\omega) = \frac{1}{4} \sum_{j=1}^{2} \left( \frac{\left( 4\lambda_j + 1 \right) \omega_0^4}{4} \right)^{\lambda_j} \frac{H_{sj}^2}{\Gamma(\lambda_j)} \frac{1}` |
| II-1-165 | part-02/ch-01 | 3 | `G(\theta) = \frac{2}{\pi} \cos^2 \theta \quad \text{for} \quad \|\theta\| < 90^{\circ}` | `G(\theta) = \frac{2}{\pi} \cos^2{\theta} \quad for \quad \|\theta\| < 90^\circ` |
| II-3-21 | part-02/ch-03 | 3 | `p(s) = -\frac{\cos\theta}{C} \frac{\partial C}{\partial x} - \frac{\sin\theta}{C} \frac{\partial C}{\partial y}` | `p(s) = -\frac{\cos\theta}{C} \left( \frac{\partial C}{\partial x} + \sin\theta \cdot \frac{\partial C}{\partial y} \right)` |
| II-5-11 | part-02/ch-05 | 3 | `\vec{\nabla} = (\partial_{\overline{\partial x}} + \partial_{\overline{\partial y}} + \partial_{\overline{\partial z}})` | `\vec{\nabla} = (\partial_{x} + \partial_{y} + \partial_{z})` |
| III-2-6d | part-03/ch-02 | 3 | `I_{\ell} = K \left( \frac{\rho g^{\frac{3}{2}}}{16 \kappa^{\frac{1}{2}}} \right) H_b^{\frac{5}{2}} \sin(2\alpha_b)` | `I_{\ell} = K \left( \frac{\rho g^{\frac{3}{2}}}{16 \kappa^2} \right)^{\frac{5}{2}} H_b^{\frac{5}{2}} \sin (2 \alpha_b)` |
| III-6-81 | part-03/ch-06 | 3 | `\overline{c} = \overline{c}_R \left( \frac{\delta_{cw}}{z_r} \right)^{\left( -\frac{w_f}{\kappa u_{*m}} \right)} \left( \frac{z}{\delta_{cw}} \right)^{\left( -\` | `\[ \bar{c} = \bar{c}_R \left( \frac{\delta_{cw}}{z_r} \right) \left( -\frac{w_f}{\kappa u_{*m}} \right) \left( \frac{z}{\delta_{cw}} \right) \left( -\frac{w_f}{` |
| V-3-2 | part-05/ch-03 | 3 | `(BCR)_{T} = \frac{\text{Total benefits}}{\text{Total, life-cycle cost}}` | `(\text{BCR})_{T} = \frac{\text{Total benefits}}{\text{Total, life-cycle cost}}` |
| V-6-21 | part-05/ch-06 | 3 | `Q_L = \sum p_i Q_i \quad for \quad Q_i \le 0` | `Q_L = \sum p_i Q_i \quad \text{for} \quad Q_i \leq 0` |
| VI-5-67 | part-06/ch-05 | 3 | `\frac{H}{\Delta D_{n50}} = (K_D \cot \alpha)^{1/3} \quad \text{or} \quad M_{50} = \frac{\rho_s H^3}{K_D \left(\frac{\rho_s}{\rho_{cr}} - 1\right)^3 \cot \alpha}` | `\frac{H}{\Delta D_{n50}} = (K_D \cot \alpha)^{1/3} \quad \text{or} \quad M_{50} = \frac{\rho_s H^3}{K_D \left(\frac{\rho_s}{\rho_w} - 1\right)^3 \cot \alpha}` |
| VI-5-139 | part-06/ch-05 | 3 | `W_{15 \text{ max}} = 0.5 W_{50 \text{ max}} = 0.75 W_{50 \text{ min}} = 1.3 W_{30}` | `W_{15\max}=0.5\ W_{50\max}=0.75\ W_{50\min}=1.3\ W_{30}` |
| VI-5-242 | part-06/ch-05 | 3 | `r = r_1 \exp(\omega \tan^{-1})` | `r = r_1 \exp(\omega \tan \theta')` |
| VI-5-261 | part-06/ch-05 | 3 | `0 . 0 1 1 < \frac { h } { \left( L _ { p } \right) _ { o } } < 0 . 0 4 5 \qquad a n d \qquad 0 . 0 1 5 < \frac { \left( H _ { m o } \right) _ { o } } { \left( L` | `0.011 < \frac{h}{(L_p)_o} < 0.045 \quad \text{and} \quad 0.015 < \frac{(H_{mo})_o}{(L_p)_o} < 0.040` |
| VI-5-293 | part-06/ch-05 | 3 | `f_D = C_D \frac{1}{2} \rho g D H^2 \left[ \frac{gT^2}{4L^2} \left( \frac{\cosh \left[ 2\pi (z+d)/L \right]}{\cosh \left[ 2pid/L \right]} \right)^2 \right] \cos ` | `f_D = C_D \frac{1}{2} \rho g D H^2 \left[ \frac{gT^2}{4L^2} \left( \frac{\cosh\left[ 2\pi(z+d)/L \right]^2}{\cosh\left[ 2\pi d/L \right]} \right) \cos\left(\fra` |
| VI-6-17 | part-06/ch-06 | 3 | `\rho_{RS} = \frac{Cov(R, S)}{\sigma_R \sigma_S} = \frac{E[(R - \mu_R) (S - \mu_S)]}{\sigma_R \sigma_S}` | `\rho_{RS} = \frac{\text{Cov}(R,S)}{\sigma_R \sigma_S} = \frac{E[(R-\mu_R)(S-\mu_S)]}{\sigma_R \sigma_S}` |
| II-1-14 | part-02/ch-01 | 2 | `C _ { 0 } \ = \ { \frac { g T } { 2 \pi } } \ = \ { \frac { 9 . 8 } { 2 \pi } } \ T \ = \ 1 . 5 6 T \ m / s` | `C_0 = \frac{gT}{2\pi} = \frac{9.8}{2\pi} T = 1.56T \text{ m/s}` |
| II-1-82 | part-02/ch-01 | 2 | `p \ = \ \mathsf { p } g \ ( y _ { s } \ - \ y )` | `p = \rho g (y_s - y)` |
| II-1-96 | part-02/ch-01 | 2 | `p \ = \ \mathsf { p } g \ ( y _ { s } \ - \ y )` | `p = \rho g (y_s - y)` |
| II-1-121 | part-02/ch-01 | 2 | `R _ { \mathfrak { n } } ( t , t + \tau ) \ = \ E [ \eta ( t ) \ \eta ( t + \tau ) ]` | `R_{\eta}(t,\ t+\tau) = E[\eta(t)\ \eta(t+\tau)]` |
| II-1-145 | part-02/ch-01 | 2 | `\boldsymbol { \mathfrak { n } } ( t ) \ = \ a \ \sin \ \omega t` | `\eta(t) = a \sin \omega t` |
| II-5-4 | part-02/ch-05 | 2 | `w \ = \ - \ \frac { a g k } { \sigma } \ \frac { \sinh \ k ( h + z ) } { \cosh k h } \ \cos ( k x - \sigma t )` | `w = -\frac{\alpha g k}{\sigma} \frac{\sinh{k(h+z)}}{\cosh{k h}} \cos{(k x-\sigma t)}` |
| II-5-24 | part-02/ch-05 | 2 | `f = f _ { D } f _ { R } f _ { \theta } f _ { \nu } f _ { L }` | `f = f_D f_R f_\theta f_v f_L` |
| II-6-5 | part-02/ch-06 | 2 | `V _ { \ m } ^ { \prime } \ = \ { \frac { A _ { \omega v g } T V _ { m } } { 2 \pi a _ { o } A _ { b } } }` | `V_{m}^{\prime }=\frac{A_{avg}\;T\;V_{m}}{2\pi a_{o}A_{b}}` |
| II-6-24 | part-02/ch-06 | 2 | `Q_{\text{max}} = \frac{2\pi}{T} a_o A_b V_{\text{max}}` | `Q_{\max} = \frac{2\pi}{T} a_o A_b V_{\max}` |
| II-6-26 | part-02/ch-06 | 2 | `Q_{1\text{max}} = \frac{Q_{\text{max}}}{1 + \frac{K_2}{K_1} + \frac{K_3}{K_1}}` | `Q_{1\max} = \frac{Q_{\max}}{1 + \frac{K_2}{K_1} + \frac{K_3}{K_1}}` |
| II-7-26 | part-02/ch-07 | 2 | `T _ { n } \, = \, 2 \, \pi \, \sqrt { \frac { m _ { \nu } } { k _ { t o t } } }` | `T_n = 2\pi\sqrt{\frac{m_v}{k_{tot}}}` |
| III-1-9 | part-03/ch-01 | 2 | `W_f = \frac{g D^2}{18 v} \left( \frac{\rho_s}{\rho} - 1 \right)` | `W_f = \frac{g D^2}{18 \nu} \left( \frac{\rho_s}{\rho} - 1 \right)` |
| III-2-7b | part-03/ch-02 | 2 | `Q_{\ell} = K \left( \frac{\rho \sqrt{g}}{16 \kappa^{\frac{1}{2}} (\rho_s - \rho) (1 - n)} \right) H_b^{\frac{5}{2}} \sin(2\alpha_b)` | `Q_{\ell} = K \left( \frac{\rho \sqrt{g}}{\frac{1}{16} \kappa^2 (\rho_s - \rho) (1-n)} \right)^{\frac{5}{2}} H_b^{\frac{5}{2}} \sin(2\alpha_b)` |
| III-3-2 | part-03/ch-03 | 2 | `\nu _ { _ { S } } \, = \, - \, { \frac { 3 \sigma k H ^ { 2 } } { 1 6 \, \sinh ^ { 2 } k h } }` | `v_s = -\frac{3\sigma kH^2}{16\sinh^2 kh}` |
| III-3-8 | part-03/ch-03 | 2 | `\tau_b = \frac{1}{4} \frac{\partial E}{\partial v} - \frac{\tau_\eta}{2} + 3 \frac{\epsilon E}{Ch^2}` | `\tau_b = \frac{1}{4} \frac{\partial E}{\partial y} - \frac{\tau_\eta}{2} + 3 \frac{\epsilon E}{Ch^2}` |
| III-3-40 | part-03/ch-03 | 2 | `V _ { _ \infty } = R _ { _ \infty } B + { \frac { S ^ { 2 } } { 2 m _ { o } } } - { \frac { 2 } { 5 } } { \frac { S ^ { \frac { 5 } { 2 } } } { 4 ^ { \frac { 3 ` | `V_{\infty} = R_{\infty} B + \frac{S^2}{2m_o} - \frac{2}{5} \frac{S^{5/2}}{A^{3/2}}` |
| III-3-45 | part-03/ch-03 | 2 | `q_{v} = K'(D - D_{*})` | `q_y = K' (D - D_*)` |
| III-6-4 | part-03/ch-06 | 2 | `z_0 = \begin{cases} \frac{v}{9u_*} & \text{for smooth turbulent flow} \\ \frac{k_n}{30} & \text{for fully rough turbulent flow} \end{cases}` | `z_0 = \begin{cases} \dfrac{\nu}{9u_*} & \text{for smooth turbulent flow} \\ \dfrac{k_n}{30} & \text{for fully rough turbulent flow} \end{cases}` |
| III-6-9 | part-03/ch-06 | 2 | `\frac{1}{4\sqrt{f_c}} + \log_{10} \frac{1}{4\sqrt{f_c}} = \log_{10} \frac{z_r u_c(z_r)}{v} + 0.20` | `\frac{1}{4\sqrt{f_c}} + \log_{10} \frac{1}{4\sqrt{f_c}} = \log_{10} \frac{z_r u_c(z_r)}{\nu} + 0.20` |
| III-6-21 | part-03/ch-06 | 2 | `f_w = \frac{2}{\sqrt{RE}}` | `f_w = \frac{2}{\sqrt{\text{RE}}}` |
| III-6-44 | part-03/ch-06 | 2 | `\mathrm { R e } _ { * } \ = \ \frac { u _ { * } k _ { n } } { \nu } \ = \ \frac { u _ { * } D } { \nu }` | `\operatorname{Re}_{*} = \frac{u_{*} k_{n}}{\nu} = \frac{u_{*} D}{\nu}` |
| V-3-8 | part-05/ch-03 | 2 | `\frac{L_s}{Y} = 0.5 \text{ to } 0.67` | `\frac{L_s}{Y} = 0.5\) to \(0.67` |
| V-4-7 | part-05/ch-04 | 2 | `W\left(\frac{A_N}{D_C}\right)^{3/2} + \left(\frac{A_N}{A_F}\right)^{3/2} < 1, \text{ Intersecting profile}` | `W\left(\frac{A_N}{D_C}\right)^{3/2} + \left(\frac{A_N}{A_F}\right)^{3/2} < 1, \text{ Intersecting profile} > 1, \text{ Nonintersecting profile}` |
| V-4-11 | part-05/ch-04 | 2 | `\frac { a } { 2 { \sqrt { \mathfrak { e } } } t }` | `\frac{a}{2\sqrt{\varepsilon}t}` |
| V-4-12 | part-05/ch-04 | 2 | `p ( t ) \, = \, 1 \, - \, \frac { \sqrt { \mathfrak { c } } t } { a \sqrt { \pi } }` | `p(t) = 1 - \frac{\sqrt{\varepsilon}t}{a\sqrt{\pi}}` |
| V-6-6 | part-05/ch-06 | 2 | `\varepsilon = \frac{K H_b^{2.5} \sqrt{g/\kappa}}{8(s-1)(1-n)(h_* + B)}` | `\varepsilon = \frac{K H_b^{25} \sqrt{g / K}}{8(s-1)(1-n)(h_* + B)}` |
| V-6-22 | part-05/ch-06 | 2 | `Q_{NET} = \Sigma(p_i Q_i) = Q_R + Q_L` | `Q_{NET} = \sum\left(p_iQ_i\right) = Q_R + Q_L` |
| VI-5-136 | part-06/ch-05 | 2 | `W_{100\,\text{max}} = 5W_{50\,\text{min}} = 8.5W_{30}` | `W_{100\max} = 5W_{50\min} = 8.5W_{30}` |
| VI-5-138 | part-06/ch-05 | 2 | `W_{50 \text{ max}} = 1.5 W_{50 \text{ min}} = 2.6 W_{30}` | `W_{50\max} = 1.5W_{50\min} = 2.6W_{30}` |
| VI-5-168 | part-06/ch-05 | 2 | `r_{F}(L,\theta) = \frac{\text{max. force, wave incident angle } \theta}{\text{max. force, head-on wave}(\theta = 0^{\circ})} = \frac{\sin\left(\frac{\pi L_{s}}{` | `r_F(L,\theta) = \frac{\max.\text{ force, wave incident angle }\theta}{\max.\text{ force, head-on wave}(\theta=0^\circ)} = \frac{\sin\left(\frac{\pi L_s}{L}\sin\` |
| VI-5-215 | part-06/ch-05 | 2 | `i = \frac { \varDelta h } { \varDelta l }` | `i = \frac{\Delta h}{\Delta l}` |
| VI-5-232 | part-06/ch-05 | 2 | `CL^{-}: q' = \frac{-6\sin\varphi_{c'rit}}{3 + \sin\varphi_{c'rit}} p'` | `\text{CL}^-: q' = \frac{-6 \sin \varphi_{c'\mathrm{rit}}}{3 + \sin \varphi_{c'\mathrm{rit}}} p'` |
| VI-5-268 | part-06/ch-05 | 2 | `\frac{S_m}{D} = 2.0 \left[ 1 - e^{-0.015(KC-11)} \right] \qquad \text{for } KC = 11` | `\frac{S_m}{D} = 2.0 \left[1 - e^{-0.015(KC-11)}\right] \quad \text{for } KC > 11` |
| VI-5-269 | part-06/ch-05 | 2 | `\frac{S_m}{D} = 2.0 \left[ 1 - e^{-0.019 (KC-3)} \right] \qquad \text{for } KC = 3` | `\frac{S_m}{D} = 2.0 \left[1 - e^{-0.019(KC-3)}\right] \quad \text{for } KC > 3` |
| VI-5-277 | part-06/ch-05 | 2 | `W = 2 . 0 H _ { i } \qquad o r \qquad W = 0 . 4 d _ { s }` | `W = 2.0 H_i \quad \text{or} \quad W = 0.4 d_s` |
| VI-6-9 | part-06/ch-06 | 2 | `P _ { f } = \iiint _ { R \leq S } \cdots \int \ f _ { _ { X _ { 1 } } } ( x _ { 1 } ) \ldots f _ { _ { X _ { n } } } ( x _ { n } ) d \ x _ { 1 } \ldots d \ x _ ` | `P_f = \iiint_{R \leq S} f_{X_1}(x_1) \ldots f_{X_n}(x_n) d x_1 \ldots d x_n` |

## Glyph fixes (kept — correct)  (8)

| Tag | Chapter | dist | Markdown | Source reading |
| --- | --- | --: | --- | --- |
| VI-5-212 | part-06/ch-05 | 7 | `\sin{\psi} = -\frac{\dot{\varepsilon}_{1} + \dot{\varepsilon}_{3}}{\dot{\varepsilon}_{1} - \dot{\varepsilon}_{3}} = \frac{\dot{\varepsilon}_{vol}}{\dot{\varepsi` | `\sin{\psi} = -\frac{\&_{1} + \&_{3}}{\&_{1} - \&_{3}} = \frac{\&_{vol}}{\&_{vol} - 2\&_{1}}` |
| II-1-146 | part-02/ch-01 | 4 | `\sigma^2 = \overline{[\eta(t)]^2} = \frac{1}{2\pi} \int_0^{2\pi} a^2 \sin^2 2\pi ft \, d(2\pi ft) = \frac{a^2}{2} = 2 \int_0^\infty E^1(f) \, df = \int_{-\infty` | `\sigma^2 = \frac{1}{2\pi} \int_0^{2\pi} a^2 \sin^2 2\pi ft \, d(2\pi ft) = \frac{a^2}{2} = 2 \int_0^\infty E^1(f) \, df = \int_{-\infty}^\infty E^2(f) \, df` |
| II-4-11 | part-02/ch-04 | 3 | `H_{mo,b} = 0.1\,L\tanh(kd)` | `H_{mo,b} = 0.1 L \tan h k d` |
| V-3-5 | part-05/ch-03 | 3 | `WTR = \frac{\text{Wall Trap Volume}}{\text{Active Sediment Volume}}` | `\text{WTR} = \frac{\text{Wall Trap Volume}}{\text{Active Sediment Volume}}` |
| II-2-10 | part-02/ch-02 | 2 | `U_g = \frac{1}{\rho_a f} \frac{dp}{dn}` | `U_g = \frac{1}{p_a f} \frac{dp}{dn}` |
| II-2-11 | part-02/ch-02 | 2 | `U_{gr} = \frac{1}{\rho_{a}f} \frac{dp}{dn} + \frac{U_{gr}^{2}}{fr_{c}}` | `U_{gr} = \frac{1}{p_a f} \frac{dp}{dn} + \frac{U^{2}_{gr}}{fr_c}` |
| II-2-31 | part-02/ch-02 | 2 | `E(f) = \frac{\alpha g^2 f^{-5}}{(2\pi)^4}` | `E(f) = \frac{\infty g^2 f^{-5}}{(2\pi)^4}` |
| II-2-32 | part-02/ch-02 | 2 | `E(f)=\frac{\alpha g^2 f^{-5}}{(2\pi)^4}\exp\left[-0.74\left(\frac{f}{f_u}\right)^{-4}\right]` | `E(f)=\frac{\infty g^2 f^{-5}}{(2\pi)^4}\exp\left[-0.74\left(\frac{f}{f_u}\right)^{-4}\right]` |

## Multi-equation crop (false positives)  (12)

| Tag | Chapter | dist | Markdown | Source reading |
| --- | --- | --: | --- | --- |
| VI-5-149 | part-06/ch-05 | 51 | `p_2 = \left\{ \begin{array}{ll} \left(1 - \frac{h_c}{\eta^*}\right) p_1 & \text{for } \eta^* > h_c \\ 0 & \text{for } \eta^* \le h_c \end{array} \right.` | `p_1 = 0.5(1+\cos\beta)(\lambda_1\alpha_1 + \lambda_2\alpha_*\cos^2\beta)\rho_w g H_{design} \] \[ p_2 = \begin{cases} \left(1-\frac{h_c}{\eta^*}\right)p_1 & \te` |
| VI-5-11 | part-06/ch-05 | 26 | `\begin{align*} &= 1.0 \qquad \text{for } 0^{\circ} \le \beta \le 10^{\circ} \\ &\gamma_{\beta} = \cos(\beta - 10^{\circ}) \qquad \text{for } 10^{\circ} < \beta ` | `\gamma_{\beta} = \begin{cases} 1.0 & \text{for } 0^\circ \leq \beta \leq 10^\circ \\ \cos(\beta - 10^\circ) & \text{for } 10^\circ < \beta \leq 63^\circ \\ 0.6 ` |
| VI-5-9 | part-06/ch-05 | 24 | `r_{B} = 1 - \frac{\tan \alpha_{eq}}{\tan \alpha}` | `r_B = 1 - \frac{\tan \alpha_{eq}}{\tan \alpha} \quad (VI-5-9) \qquad r_{dB} = 0.5 \left( \frac{d_B}{H_s} \right)^2, \quad 0 \leq r_{dB} \leq 1` |
| VI-5-148 | part-06/ch-05 | 24 | `p_1 = 0.5(1 + \cos\beta)(\lambda_1 \alpha_1 + \lambda_2 \alpha_* \cos^2\beta) \rho_w g H_{design}` | `\eta = 0.75(1+\cos\beta)\lambda_1 H_{design} \quad (\text{VI}-3-148) \] \[ p_1 = 0.5(1+\cos\beta)(\lambda_1\alpha_1 + \lambda_2\alpha_*\cos^2\beta) \rho_w g H_{` |
| II-1-171 | part-02/ch-01 | 22 | `\mu_{j_1} = \frac{1}{q} \quad ; \quad q = 1 - p \quad ; \quad \sigma_{j_1} = \frac{\sqrt{1 - q}}{q}` | `\mu_{j_1} = \frac{1}{q}; \quad q = 1 - p; \quad \sigma_{j_1} = \frac{\sqrt{1-q}}{q}; \] \[ p = p(H>H_c) = \exp\left[-\frac{1}{8}\eta_c^2\right]; \quad \eta_c = ` |
| V-5-4 | part-05/ch-05 | 19 | `F_L = \frac{V_L}{\sqrt{gh}}` | `F_L = \frac{V_L}{\sqrt{gh}} \approx 8 \cos^3 \left[ \frac{\pi}{3} + \frac{1}{3} \cos^{-1} \left( 1 - \frac{1}{B_R} \right) \right]^{1/2} \quad (\text{rectangula` |
| II-1-169 | part-02/ch-01 | 15 | `R_{H} = \frac{1}{\sigma_{0}} \frac{1}{N-k} \sum_{i=1}^{N-k} (H_{i} - \mu)(H_{i+k} - \mu)` | `R_H = \frac{1}{\sigma_0} \cdot \frac{1}{N-k} \sum_{i=1}^{N-k} (H_i - \mu)(H_{i+k} - \mu) \] \[ \sigma_0 = \frac{1}{N} \sum_{i=1}^N (H_i - \mu)^2` |
| V-5-8 | part-05/ch-05 | 15 | `W = 90 + 0.03 (N_B - 1000)` | `W = 90 + 0.03 (N_B - 1000) \quad \text{in meters} \] \[ W = 300 + 0.1 (N_B - 1000) \quad \text{in feet}` |
| V-5-3 | part-05/ch-05 | 14 | `Z = 0.2125 C_B \frac{B}{L} \frac{T}{h} V^2 \qquad V \text{ in knots}, Z \text{ in ft}` | `Z = 0.2125 C_B \frac{B}{L} \frac{T}{h} V^2 \quad \text{V in knots, Z in ft} \] \[ Z = 0.01888 C_B \frac{B}{L} \frac{T}{h} V^2 \quad \text{V in km/hr, Z in m}` |
| V-5-7 | part-05/ch-05 | 10 | `W = W_{\mathrm{min}} + 0.10 \ N_B \qquad \text{in feet}` | `W = W_{\text{min}} + 0.03 N_B \quad \text{(in meters (interior channels))} \] \[ W = W_{\text{min}} + 0.10 N_B \quad \text{(in feet)}` |
| V-4-14 | part-05/ch-04 | 8 | `p ( t ) \ = \ 1 - \left( \frac { \sqrt { \epsilon t } } { a \sqrt { \pi } } + \frac { E t } { \Delta y _ { o } } \right)` | `p(t) = 1 - \left( \frac{\sqrt{\epsilon} t}{a \sqrt{\pi}} + \frac{Et}{\Delta y_o} \right) \] \[ 0.5 < p(t) < 1.0` |
| III-6-5 | part-03/ch-06 | 7 | `\frac{k_n u_*}{v} \ge 3.3 \quad \text{for fully rough turbulent flow}` | `\frac{k_n u^*}{v} \geq 3.3 \quad \text{for fully rough turbulent flow} \] \[ \frac{k_n u^*}{v} \leq 3.3 \quad \text{for fully smooth turbulent flow}` |
