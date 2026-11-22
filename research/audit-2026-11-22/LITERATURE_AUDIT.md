# تدقيق أولي للأسبقية العلمية — 22/11/2026

**الصفة:** مراجعة أدبيات مبدئية وليست إثباتًا لعدم وجود عمل سابق. **المرجع المدروس:** `main@cb3383e0c3b553d9236d2b8968e5784b68fac2ab`.

## ملخّص القرار
**لا توجد في هذه المرحلة مبرهنة أمكن إثبات جدّتها بعد مقارنة مستقلة بالأدبيات**. توجد مسارات ضيقة لاستنباط مسائل محتملة، ولكن يجب إثبات اختلافها عن المعلوم أو إيجاد تحسين غير بديهي. يشبه تركيب النتائج الحالية بصورة وثيقة جبر الأنواع، وتكافؤ السياقات، وذاكرة المنشأ، والمونويدات التبديلية الحرة، وتقسيمات الأعداد، واسترجاع المجموعات من مجاميع القوى.

لا نعني بقولنا «معروف في الإطار العام» أن مسلمات المؤسس مساوية حرفيًا لمسلّمات أي مرجع؛ المقارنة بين *نتائج* محددة أولًا. وقد يكون النظام الجزئي ذا تفاصيل خاصة، ولكن التفاصيل وحدها ليست برهان أصالة.

## مصفوفة المقارنة

| نتيجة/مفهوم بالمشروع | نطاق النظرية المنشورة | نوع التشابه | حكم مبدئي | عمل لازم قبل ادعاء أصالة |
|---|---|---|---|---|
| نمذجة كل طبيعة بنوع وقواعد عمليات بين الأنواع | Many-/order-sorted universal algebra and partial operations | مباشر من حيث البنية | **مشابه معروف** | بيان ما تفرضه مسلمة التنافي فوق التوقيع المختار |
| شجرة الضرب القابلة للفك إلى عاملين مرتبين | Free/term algebras, constructors with left/right projections | مباشر في النموذج الحر | **ليس جديدًا وحده** | مبرهنة تخصّ تفاعل الفك مع مساواة/توزيع غير حرّ |
| قياسان متساويان وسجلّان مختلفان | Provenance semantics, lineages, symbolic computations | مباشر مبدئيًا | **مشابه معروف** | فصل النموذج عن provenance semirings ومناقشة التبديليّة |
| تكافؤ كل السياقات وتعويض عنصر بآخر داخل عمليات | Syntactic congruence / tree automata / contextual equivalence | مباشر مبدئيًا | **مشابه معروف** | صياغة قيد جديد للفكّ على خارج القسمة وثبوته |
| حدّ عدد تجارب التعليمات الخطية بفضل فضاء الأسطر | Weighted automata and linear-algebraic minimization | مباشر | **تخصص لمعلوم** | إظهار تعميم لا يغطيه تحليل فضاء الوصول |
| تصغير حالات القبول بواسطة البواقي | Finite automata minimization / Myhill–Nerode | مباشر | **تخصص لمعلوم** | تعقيد الخوارزمية في نموذج جديد أو حدّ أدنى خاص |
| دمج سجلات دفعات متطابقة مع تجاهل الترتيب | Free commutative monoid / finite multisets | مباشر | **معلوم** | أحكام خاصة بتفاعل جمع الدفعات مع ضرب قابل للفك |
| تقسيم العدد الإجمالي إلى أحجام دفعات موجبة | Integer partition function p(n) | مباشر | **معلوم** | مثال قيد جديد أو تعقيد حسابي غير معروف |
| فك أحجام K دفعات من مجاميع القوى | Newton identities; inverse power sum problem | مباشر | **معروف** | لا تصلح كدعوى سبق بحدّ ذاتها |
| تصادم مجاميع قوى عديدة مع اختلاف المجموعات | Prouhet–Tarry–Escott problem | مباشر | **مجال عريق ونشط** | تجنب اعتبار أمثلة تصادم جديدة من تلقائها |
| ترميز سجل بإضافة بتّات بحسب حجم الليف المشترك | Counting/zero-error coding with side information | مضمون عام معروف | **غير أصيل وحده** | حدود دقيقة جديدة في صنف بنى غير مدروس |

## المصادر الأولية المحققة
1. J. A. Goguen and J. Meseguer, **Order-sorted algebra I: equational deduction for multiple inheritance, overloading, exceptions and partial operations**, *Theoretical Computer Science* 105(2), 217–273 (1992). https://www.sciencedirect.com/science/article/pii/030439759290302V
2. **Semantics of order-sorted specifications**, *Theoretical Computer Science* 94(1), 1–35 (1992). https://www.sciencedirect.com/science/article/pii/0304397592903227
3. Todd J. Green, Grigoris Karvounarakis, Val Tannen, **Provenance Semirings**, PODS 2007, 31–40. DOI: 10.1145/1265530.1265535. Manuscript: https://www.cs.ucdavis.edu/~green/papers/pods07.pdf
4. Hubert Comon et al., **Tree Automata Techniques and Applications**, 2008. University listing: https://pro.univ-lille.fr/remi-gilleron/publications ; DOI-like record via HAL: https://inria.hal.science/hal-03367725v1
5. Stefan Kiefer, **Notes on Equivalence and Minimization of Weighted Automata** (2020), arXiv:2009.01217. https://arxiv.org/abs/2009.01217
6. Vikraman Choudhury, Marcelo Fiore, **Free Commutative Monoids in Homotopy Type Theory** (2023), DOI: 10.46298/entics.10492. https://entics.episciences.org/10492
7. Hana Melánová, Bernd Sturmfels, Rosa Winter, **Recovery from Power Sums** (published online 23/04/2022), DOI: 10.1080/10586458.2022.2061650. https://www.tandfonline.com/doi/full/10.1080/10586458.2022.2061650
8. **DLMF §27.14, Unrestricted Partitions**, NIST. https://dlmf.nist.gov/27.14
9. **The Prouhet Tarry Escott Problem: A Review** (2019), *Mathematics* 7(3):227. https://doi.org/10.3390/math7030227
10. **Ideal solutions in the Prouhet–Tarry–Escott problem**, arXiv:2304.11254 (2023). https://arxiv.org/abs/2304.11254
11. **The Prouhet--Tarry--Escott problem for subsets with small doubling in integral domains**, arXiv:2609.05061 (2026). https://arxiv.org/abs/2609.05061
12. **Foundations of Reversible Computation** (2020), survey, Springer. https://doi.org/10.1007/978-3-030-47361-7_1
13. **Side Information Design in Zero-Error Coding for Computing** (2024). https://pmc.ncbi.nlm.nih.gov/articles/PMC11049120/

## أربعة تحذيرات منهجية
- «لم أعثر» لا تعني «غير منشور». يجب إعادة البحث في MathSciNet/zbMATH/Google Scholar/semantic search وتتبّع المراجع الخلفية والأعمال الأحدث قبل أي إرسال لمجلة.
- تعميم مختلف في التسمية فقط ليس إنجازًا أصيلًا؛ يجب وضع المبرهنة المرشحة إلى جوار أقرب مبرهنة معروفة وصياغة الفرق الصوري.
- واجب الفصل بين **مساواة السجل الكامل** و**مساواة نتيجة القياس** و**التكافؤ السياقي**، وإلا تنتقل استنتاجات خاطئة بين مستويات مختلفة.
- لا يمثّل اختبار 1000 حالة برهانًا لحالة لا نهائية، ولا يكفي مرور اختبار محلي لمنح حكم مراجعة مستقلة.

## ترتيب المسارات بحسب احتمال إضافة مبرهنة غير روتينية
A. **التوافق بين التكافؤ السياقي والفكّ على خارج القسمة للعمليات ذات الأنواع**: احتمال بحثي مشروط، لأن عناصره معروفة أصلًا؛ يلزم ابتكار حدّ فعلي أو حالة عدم وجود/وحدانية ذات مضمون.
B. **التوزيع على عامل واحد مع الاسترجاع وقيود الصفر/الجمع**: احتمال تخصص، لكن برهان الوجود بوساطة جداول المعدلات نموذج للمونويد الحر؛ يلزم تجاوز هذا المثال.
C. **أقل ذاكرة قابلة للتحديث محليًا عبر سلاسل مختلطة**: أنسب لاستكشاف خوارزمي/حاسوبي مع حدّين متقابلين؛ يجب مقارنة العمل بخوارزميات provenance وتصغير الآلات.
D. **ترميز تقسيمات العلب ومجاميع القوى**: نتيجة معظمها كلاسيكية؛ لا تُفضَّل مسألة منشورة مباشرة إلا عند ظهور تعميم متميز موثّق.

**قرار الجولة:** لا مسوّدة منشورة بعنوان «نظرية جديدة» الآن؛ نؤسس أولًا إطارًا مبرهنًا ونبحث بصرامة عن فرضية ضيقة مبتكرة. المرجع التفصيلي: `RESEARCH_GATE.md`.
