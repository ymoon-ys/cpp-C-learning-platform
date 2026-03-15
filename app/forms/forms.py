from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, Regexp


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=1, max=50, message='用户名长度应在1-50个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空')
    ])


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=3, max=20, message='用户名长度应在3-20个字符之间'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='用户名只能包含字母、数字和下划线')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, max=50, message='密码长度应在6-50个字符之间')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    role = SelectField('角色', choices=[
        ('student', '学生'),
        ('teacher', '教师')
    ], validators=[DataRequired(message='请选择角色')])


class UserProfileForm(FlaskForm):
    nickname = StringField('昵称', validators=[
        Optional(),
        Length(max=50, message='昵称长度不能超过50个字符')
    ])
    email = StringField('邮箱', validators=[
        Optional(),
        Email(message='请输入有效的邮箱地址')
    ])


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('原密码', validators=[
        DataRequired(message='请输入原密码')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=6, max=50, message='密码长度应在6-50个字符之间')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请确认新密码'),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])


class CourseForm(FlaskForm):
    title = StringField('课程标题', validators=[
        DataRequired(message='课程标题不能为空'),
        Length(min=2, max=100, message='课程标题长度应在2-100个字符之间')
    ])
    description = TextAreaField('课程描述', validators=[
        Optional(),
        Length(max=2000, message='课程描述长度不能超过2000个字符')
    ])
    category = StringField('分类', validators=[
        Optional(),
        Length(max=50, message='分类长度不能超过50个字符')
    ])


class ChapterForm(FlaskForm):
    title = StringField('章节标题', validators=[
        DataRequired(message='章节标题不能为空'),
        Length(min=1, max=100, message='章节标题长度应在1-100个字符之间')
    ])
    order_index = IntegerField('排序', validators=[
        Optional(),
        NumberRange(min=0, max=9999, message='排序值应在0-9999之间')
    ])


class LessonForm(FlaskForm):
    title = StringField('课时标题', validators=[
        DataRequired(message='课时标题不能为空'),
        Length(min=1, max=100, message='课时标题长度应在1-100个字符之间')
    ])
    description = TextAreaField('课时描述', validators=[
        Optional(),
        Length(max=1000, message='课时描述长度不能超过1000个字符')
    ])
    content = TextAreaField('课时内容', validators=[
        Optional(),
        Length(max=50000, message='课时内容长度不能超过50000个字符')
    ])
    content_type = SelectField('内容类型', choices=[
        ('text', '文本'),
        ('video', '视频'),
        ('document', '文档'),
        ('image', '图片')
    ], validators=[DataRequired(message='请选择内容类型')])
    duration = StringField('时长', validators=[
        Optional(),
        Length(max=20, message='时长长度不能超过20个字符')
    ])
    order_index = IntegerField('排序', validators=[
        Optional(),
        NumberRange(min=0, max=9999, message='排序值应在0-9999之间')
    ])


class ProblemForm(FlaskForm):
    title = StringField('题目标题', validators=[
        DataRequired(message='题目标题不能为空'),
        Length(min=2, max=200, message='题目标题长度应在2-200个字符之间')
    ])
    description = TextAreaField('题目描述', validators=[
        DataRequired(message='题目描述不能为空'),
        Length(max=10000, message='题目描述长度不能超过10000个字符')
    ])
    input_format = TextAreaField('输入格式', validators=[
        Optional(),
        Length(max=1000, message='输入格式长度不能超过1000个字符')
    ])
    output_format = TextAreaField('输出格式', validators=[
        Optional(),
        Length(max=1000, message='输出格式长度不能超过1000个字符')
    ])
    sample_input = TextAreaField('样例输入', validators=[
        Optional(),
        Length(max=1000, message='样例输入长度不能超过1000个字符')
    ])
    sample_output = TextAreaField('样例输出', validators=[
        Optional(),
        Length(max=1000, message='样例输出长度不能超过1000个字符')
    ])
    difficulty = SelectField('难度', choices=[
        ('简单', '简单'),
        ('中等', '中等'),
        ('困难', '困难')
    ], validators=[Optional()])
    time_limit = IntegerField('时间限制(秒)', validators=[
        Optional(),
        NumberRange(min=1, max=300, message='时间限制应在1-300秒之间')
    ])
    memory_limit = IntegerField('内存限制(MB)', validators=[
        Optional(),
        NumberRange(min=1, max=1024, message='内存限制应在1-1024MB之间')
    ])
    hint = TextAreaField('提示', validators=[
        Optional(),
        Length(max=1000, message='提示长度不能超过1000个字符')
    ])


class DiscussionForm(FlaskForm):
    title = StringField('帖子标题', validators=[
        DataRequired(message='帖子标题不能为空'),
        Length(min=2, max=100, message='帖子标题长度应在2-100个字符之间')
    ])
    content = TextAreaField('帖子内容', validators=[
        DataRequired(message='帖子内容不能为空'),
        Length(min=2, max=10000, message='帖子内容长度应在2-10000个字符之间')
    ])
    category = SelectField('分类', choices=[
        ('question', '提问'),
        ('share', '分享'),
        ('discussion', '讨论'),
        ('other', '其他')
    ], validators=[Optional()])


class ReplyForm(FlaskForm):
    content = TextAreaField('回复内容', validators=[
        DataRequired(message='回复内容不能为空'),
        Length(min=1, max=2000, message='回复内容长度应在1-2000个字符之间')
    ])


class CodeShareForm(FlaskForm):
    title = StringField('标题', validators=[
        DataRequired(message='标题不能为空'),
        Length(min=2, max=100, message='标题长度应在2-100个字符之间')
    ])
    code = TextAreaField('代码', validators=[
        DataRequired(message='代码不能为空'),
        Length(min=1, max=50000, message='代码长度不能超过50000个字符')
    ])
    description = TextAreaField('描述', validators=[
        Optional(),
        Length(max=1000, message='描述长度不能超过1000个字符')
    ])
    language = SelectField('编程语言', choices=[
        ('cpp', 'C++'),
        ('c', 'C'),
        ('python', 'Python'),
        ('java', 'Java'),
        ('javascript', 'JavaScript'),
        ('other', '其他')
    ], validators=[DataRequired(message='请选择编程语言')])
    tags = StringField('标签', validators=[
        Optional(),
        Length(max=100, message='标签长度不能超过100个字符')
    ])


class AssignmentForm(FlaskForm):
    title = StringField('作业标题', validators=[
        DataRequired(message='作业标题不能为空'),
        Length(min=2, max=100, message='作业标题长度应在2-100个字符之间')
    ])
    description = TextAreaField('作业描述', validators=[
        Optional(),
        Length(max=2000, message='作业描述长度不能超过2000个字符')
    ])
    problem_id = IntegerField('关联题目ID', validators=[
        DataRequired(message='请选择关联题目'),
        NumberRange(min=1, message='题目ID必须大于0')
    ])
    start_time = StringField('开始时间', validators=[Optional()])
    end_time = StringField('结束时间', validators=[Optional()])
