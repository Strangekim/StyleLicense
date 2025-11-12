from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

try:
    google_app = SocialApp.objects.get(provider='google')
    site = Site.objects.get(id=1)

    print(f"'{google_app.name}' 앱과 '{site.domain}' 사이트를 찾았습니다.")
    print("이제 관계를 재설정합니다...")

    google_app.sites.set([site])

    print("\n성공: 'google' 앱의 사이트 연결을 성공적으로 재설정했습니다.")
    print("이제 서버를 재시작하고 다시 시도해 보세요.")

except Exception as e:
    print(f"오류 발생: {e}")

