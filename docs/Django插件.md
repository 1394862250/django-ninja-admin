| **插件名**                                        | **框架作用**                                                                      | **热度（受欢迎程度）**                             |
| ---------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------- |
| Django Allauth                                 | 提供用户登录、注册、密码找回、邮箱验证及第三方 OAuth 社交账号登录等全套认证功能，增强了 Django 内置认证模块                 | GitHub标星约 **10.2k**（功能全面的账户认证套件）          |
| Django Guardian                                | 实现按对象粒度（Object-Level）的权限控制，弥补 Django 默认权限只能按模型的不足                             | GitHub标星约 **3.8k**（细粒度权限管理流行）             |
| Django OAuth Toolkit                           | 提供 OAuth2 授权服务器功能，可与 Django/DRF 集成，方便地为应用添加基于 OAuth2 的认证与授权支持                 | GitHub标星约 **3.3k**（主流 OAuth2 实现方案）        |
| **Celery**                                     | 功能强大的分布式异步任务队列，支持将耗时任务放入队列后台执行，并可定时调度任务，适用于处理大量任务的生产环境                        | GitHub标星约 **27.5k**（Python 领域最流行的异步任务框架）  |
| Django Debug Toolbar                           | 可嵌入页面显示调试面板，包括SQL查询、请求/响应信息、模板渲染时间等调试数据，辅助开发者分析性能瓶颈                           | GitHub标星约 **8.3k**（Django 调试必备工具）         |
| Django Storages                                | 提供对接多种外部存储后端的统一接口，便捷地将静态文件和媒体文件保存到如 Amazon S3 等云存储服务                          | GitHub标星约 **2.9k**（常用的静态/媒体文件存储方案）        |
| Django Pipeline                                | 前端静态资源打包管道，支持合并压缩 CSS/JS、使用各种预处理器，简化 Django 项目的资源管理和部署                        | GitHub标星约 **1.5k**（经典的静态文件打包优化工具）         |
| Django Compressor                              | 将模板中的 CSS/JS 代码压缩合并为单一文件，以减少请求次数，加速页面加载                                       | GitHub标星约 **2.9k**（常用的前端资源压缩工具）           |
| Django Reversion                               | 为 Django 模型提供版本控制，可记录模型数据变更历史并支持回滚恢复                                          | GitHub标星约 **3.1k**（模型数据版本追踪利器）            |
| Django Extensions                              | 扩展了大量 Django 实用功能的合集，包括增强的模型字段、管理命令（如 runserver_plus）等，加速开发调试                 | GitHub标星约 **6.8k**（功能丰富的开发辅助工具集）          |
| Django Braces                                  | 提供一组可重用的 CBV（类视图）Mixin 组件，涵盖常见的视图功能（登录验证、表单处理等），减少样板代码                        | GitHub标星约 **2k**（提高类视图开发效率的工具）            |
| Django Haystack                                | 功能完备的全文检索引擎框架，支持 Whoosh、Solr、Elasticsearch 等后端，方便在 Django 中实现全文搜索功能           | GitHub标星约 **3.7k**（主流的搜索集成方案）             |
| Django CKEditor                                | 集成开源富文本编辑器 CKEditor，提供 `RichTextField` 等方便在 Django 管理后台或表单中使用所见即所得富文本         | GitHub标星约 **2.5k**（常用的富文本编辑器插件）           |
| Django ImageKit                                | 自动化图片处理库，可在保存模型对象时按配置生成缩略图、裁剪、压缩和添加水印等，多用于头像等图片的动态处理                          | GitHub标星约 **2.3k**（图片缩略图与处理工具）            |
| Django Xadmin                                  | 基于 Bootstrap 美化并增强默认 Admin，提供主题界面、自定义过滤器等高级功能，让 Django 后台更强大美观                | GitHub标星约 **4.8k**（流行的第三方 Admin 管理界面）     |
| Django Constance                               | 实现应用配置项的动态化管理，可将项目中的部分设置存储在数据库并通过管理后台实时修改，而无需重启服务器                            | GitHub标星约 **1.8k**（方便配置参数动态调整）            |
| Django Model Utils                             | 提供常用模型工具集，例如时间戳模型 `TimeStampedModel`、状态机字段等，可直接继承使用，减少自定义模型重复代码               | GitHub标星约 **2.7k**（实用的模型辅助组件库）            |
| Django Crispy Forms                            | 大幅改进表单渲染，允许以 DRY 方式构建可复用的表单布局，并支持 Bootstrap 等前端框架美化表单输出                       | GitHub标星约 **5.1k**（表单布局美化与DRY表单利器）        |
| Django MPTT                                    | 以高效的改进前序遍历树（MPTT）算法储存和管理树形数据，可方便实现多级评论、类别等树结构模型                               | GitHub标星约 **3k**（树形数据模型处理标准方案）            |
| Django Notifications (django-notifications-hq) | 实现站内通知功能，可生成类似 GitHub 通知的消息流，包括未读通知计数、标记已读等机制                                 | GitHub标星约 **1.9k**（通用的站内通知框架）             |
| Django Simple Captcha                          | 为 Django 表单添加验证码字段的简易方案，支持高度自定义的图片验证码，常用于注册等防机器人提交场景                          | GitHub标星约 **1.4k**（轻量级图形验证码插件）            |
| Django Anymail                                 | 统一整合多家邮件发送服务（如 Mailgun、SendGrid 等）的 Django 邮件后端，开发者可用同一接口调用不同服务发送邮件           | GitHub标星约 **1.8k**（灵活的第三方邮件服务集成）          |
| Django Activity Stream                         | 通用的用户动态流应用，可追踪站点上的动作并生成“朋友圈”或用户关注的动态墙，支持 Actor-Verb-Target 模型                 | GitHub标星约 **2.4k**（社交类网站动态_feed_生成利器）     |
| Django Channels                                | 将 Django 扩展为支持 WebSocket 等异步通信的框架，实现长连接、实时通知等功能；借助 ASGI 提供异步能力                | GitHub标星约 **6.3k**（官方支持的异步消息通信框架）         |
| Django Redis                                   | 基于 Redis 的高速缓存后端，实现对 Django 缓存和会话的全面支持，用法与默认缓存类似但性能更佳                         | GitHub标星约 **3k**（Django 最常用的 Redis 缓存接口）  |
| Django Cacheops                                | 提供自动化的 ORM 查询集结果缓存，支持基于信号的细粒度失效机制，可显著提升数据库查询性能                                | GitHub标星约 **2.2k**（ORM级别缓存提升查询效率）         |
| Graphene-Django                                | 将 GraphQL 查询语言融入 Django 项目，提供对 Django ORM 的无缝支持，可自动生成 GraphQL Schema，并结合权限系统等 | GitHub标星约 **4.4k**（流行的 Django GraphQL 实现） |
| Django Silk                                    | Django 的实时性能分析和查询剖析工具，中间件拦截所有请求和数据库操作并提供可视化界面，便于定位性能瓶颈                        | GitHub标星约 **4.9k**（性能调优与分析的利器）            |
| Django Grappelli                               | 提供美观响应式的 Django 管理后台皮肤与增强功能，基于网格布局，支持主题定制、下拉过滤等，使默认 Admin 界面更现代友好             | GitHub标星约 **3.9k**（知名的后台界面美化扩展）           |
