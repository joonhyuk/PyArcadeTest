---
aliases: NG1, escape
tags: game-dev
---

# Project Info
- [[Escape]] 개발 문서
- [[python.arcade|arcade]], [[python.pymunk|pymunk]] 사용

## Goal
- rapid prototyping에 적합한 프레임워크를 갖춘다.
- 게임디자인이 적용된 샘플들을 만든다.

## Full Roadmap
1. 괜찮은 게임을 만든다.
2. 1을 엔진(프레임워크) 없이 만든다.
3. 2에서 컨텐츠를 제거하면 엔진(프레임워크)이 된다.

## Framework Requirement
- 기존 상용 엔진에서 제공하는 게임 오브젝트 구조를 참고하여 편리한 프로토타이핑이 가능하도록 한다.
- 가능한 저수준의 모듈만 링크하여 사용한다. [[python.pymunk|pymunk]]와 pyglet은 각각 Havoc, DirectX의 위상처럼 그대로 간다.
- Windows, Mac, Linux 크로스플랫폼을 유지한다.
- PIP repo에 등록 가능하도록 표준 요소를 갖춘다.


# Game Design
[[Escape]] 참고


# Source tree

## lib.foundation
- 공용 라이브러리

## lib.escape
- 게임 요소 전용 라이브러리

## resources
- 바이너리 애셋 데이터

## data
- 넌바이너리 애셋 데이터


# Engine Structure

![[game structure.excalidraw]]

- 한 프레임에서 벌어지는 일 ;
	- 게임 클라이언트에서 이벤트 발생(조작 입력)
	- 각 액터의 controller tick 실행
		- 플레이어의 경우는 조작을 받아서, AI는 blackboard - BT의 결과로.
		- controller는 액션을 발동하거나, 이동을 설정하거나, 시스템 콜을 하거나.
			- 액션의 경우 action handler를 통해 movement를 제어할 수 있음.
	- 각 액터의 movement handler tick 실행
		- 설정된 이동을 프레임 단위로 실행 (매 프레임마다 force를 줘야 하기 때문)
	- 게임 운영 규칙 체크
	- 물리 시뮬레이션
		- 필요시(충돌 등) 바디 단위에서 설정한 콜백 실행
		- physics 와 sprite 싱크
	- 렌더링


## Inputs - PlayerController
- 키보드, 마우스, 게임패드 입력 처리 구조 및 PlayerController와의 관계.
	- PlayerController(이하 pc)는 게임 내에서 플레이어가 spawn되지 않으면 만들어지지 않는다. 따라서 아웃게임에서의 입력 처리가 필요.
		- 아웃게임은 scene 단위이므로 client에서 이벤트를 받고 scene에 직접 명령을 내리거나(move_cursor_down() 처럼) 아니면 각 scene에서 ui용 pc를 갖고 있거나.
		- 나중에 ui 만들때 고민한다.
- 조작 수단은 키보드+마우스 또는 게임패드 둘 중 하나만 사용 가능.
	- 컨트롤러 중간에 연결하거나 빼는 것도 나중에 지원. 일단은 게임 시작 시점의 attached 여부로만.
	- 조작 매핑은 키마, 게임패드 두 가지로 제공.
		- `{inputs.evade : (keys.SPACE, joybuttons.A)}`
		- 액션 펑션 매핑 : `{inputs.evade : actions.evade}`


### 입력 매핑
- 설정을 만들어 지원하는 것은 나중 일이겠지만 간단하게 구조라도 만들어 두면 좋을 듯.
- 현재는 그냥 `on_key_press(key:int)`와 같이 직접 이벤트 콜을 받는 함수에서 직접 if문으로 체크하여 실행중.
- pc가 액터에 명령을 내리는 구조는 단순하게 `owner.actions.<액션명>(args)`인데, ide의 자동완성 때문에...(하지만 그마저 완전하지 않은게, 액션의 작동구조 때문에 doc나 내부 arg의 힌팅은 지원되지 않는다.)
- 액션의 종류를 미리 enum으로 정해두고 한단계 거쳐서 매핑하는게 맞기는 한데, (`A버튼 -> "회피액션" -> actions.evade(speed = 100)`) 매핑테이블을 어떻게 구성하는게 커스터마이징이 쉬울지.
- import 구조와 맞물려서 복잡해질 수 있으니 잘 생각해봐야 함.


## MObject
- 게임 내 사물의 기본이 되는 오브젝트. 게임에서 등장하는 모든 것의 라이프사이클 표준을 정의한다.

### as-is
lifetime과 각종 active 상태 관리에 주력했음.
- init : 멤버 변수 정의, on_init 실행
	- kwargs 관리 : 그닥 실용적이지 못한 느낌?
	- `id` : 그냥 필요시 id()로 얻을 수 있기는 한데...
	- `_alive, _update_tick, _spawned` : 복잡하긴 한데, 셋 다 true여야 tick이 실행된다?
- spawn : 라이프타임 있는 경우 타이머 시작, on_spawn 실행
	- 라이프타임은 별로 필요 없어보임. 차라리 별도의 컴포넌트로 관리하는게 낫지 않을까.
- destroy : 기초 멤버 변수들 False로 세팅하고 타이머 삭제, on_destroy 실행

### to-be
이름을 아예 그냥 GameObject로 바꾼다.
- init : 생성. 언제 어디에서 해도 무방
- setup : 기초 작업. 별도의 컴포넌트를 세팅하거나 변수를 오버라이딩 하거나.
- spawn : 월드(정확히는 ObjectLayer)에 꺼내놓는 것. 스폰 되어야 tick이 돈다.
- tick
- destroy

현재 겪는 어려움이 무엇인가? 뭐라도 좋아지는게 있어야 바꾸지. 기분만이라도...

### spawn structure
- (방식 1) 액터 오브젝트 생성, 생성시 스폰 혹은 생성 후 스폰.
- 스폰은, 등록된 각 컴포넌트를 스폰시키는 역할이 핵심.
- 가장 중요한 body의 경우, body 생성 시점에 트랜스폼을 함께 설정하거나, 스폰시키면서 설정한다.

## Actor
- controller : tick마다 무엇을 할지 결정하고 actor에게 명령을 내린다. 정확히는, actor의 각 컴포넌트들에게 명령을 내리는 것. 여전히 컴포넌트를 actor에 융합(?) 시키는 방식이 땡기는데... 보일러플레이팅 노가다가 너무 심하다.

## PlayerController
- 게임 실행 시 local player controller를 등록?
- 입력 이벤트 받는 곳에서 등록된 local player controller의 입력 처리를 실행? ENV와의 관계는?
	- ENV는 사실 없는게 맞다. 컨트롤러 정보 get 하는 용도로 역할을 단순화 하는 것도... 또는 그냥 전부 App에 통합시키는 것도 고려해 봐야 한다.
	- scene 개념에서 보면 언리얼의 레벨인데, 게임오브젝트에서 사용할 맵과 플레이어 컨트롤러를 들고 있다.
	- 즉, view에서 자신이 on_show 할 때 self.window에 플레이어 컨트롤러를 세팅? 각 캐릭터는 자신이 로컬 플레이어일 때 플레이어 컨트롤러에 빙의당한다? 플레이어 컨트롤러는 모든 플레이어 액션을 정의하여 가지고 있고, 명령을 받는 것은 각 로컬에서? 리플리케이션 구조를 따로 들고 있지 않고 App이 로컬의 플레이어컨트롤러를 작동시키거나 서버의 플레이어컨트롤러에 명령을 전송?
	- 나중에 네트워크 멀티플레이 도입하게 되면 심각하게 뒤집어야 할 것. 렌더링을 완전히 분리해야 할 수도.
		- 물리 시뮬레이션을 서버에서 돌려야 하는데, 이게 가능한 일인지조차 알 수 없음. 멀티플레이를 고려하면 애초에 pymunk를 쓰면 안될지도.
		- 서버에서 돌리려면 모든 물리 세팅 코드가 클라이언트에서 분리되어 존재해야 함. 서버에서는 arcade를 쓰지 않는다. (현재 arcade에 injecting 하는 코드(deprecation 예정)를 제외하면 그렇게 되어있음.)
- 강렬한 유혹 : 액션을 컨트롤러에 통합. 직관성은 떨어지지만 생산성이 올라간다.
	- 아니면 컨트롤러에서 액션 클래스를 상속 받아버리는거지. 어차피 바디는 같으니.

## Action
attack-melee, attack-projectile, evade, open, ...
- 액션 요구사항
	- owner는 body를 가진 액터로 제한된다. (transform을 가진다)
	- 쉽게 호출 가능해야 하고, 불러올 때 타입힌팅을 지원해야 한다.(이름, 매개변수들, doc)
	- 타임라인이 있고, 작동 중 다른 액션을 블락할 수 있어야 한다. (default : block_all)
	- 셀프 쿨타임이 있어야 하는가?
		- 
	- 이동, 회전 제약이 가능해야 한다.
	- pre, main, post로 구분.
- 개별 액션을 클래스화 하는데는 성공. 이걸 액터에 심을지 액터컴포넌트에 심을지 고민 중.
	- 액션 제어를 위해서는 액터 컴포넌트에 하는게 낫기는 한데...
	- 발동은 컨트롤러에서 직접 owner 불러서 호출하도록 하고, 액션 핸들러는 참조 역할만?

## MovementHandler
- 위치 이동과 회전을 담당.
	- shape transform(스케일링 등)과 애니메이션까지 담당하게 하는건 오바... 별도의 컴포넌트를 만든다.
- 이동 속력 모드가 있고 기어 변속하듯이 전환이 가능하다.
	- 세팅할 때 직관적이지 않다. crawl, walk, run, sprint처럼 할 수 없으려나.
	- 이동 속도는 액터에 따라 설정된다. 게임 conf에서 튜플로 저장.

### move
- `move(direction:Vector, )`


# Bugs
- (SOLVED) physics hide시 해제가 안되는 경우가 있음.
	- 작은 공과 충돌하는 상황에서는 몇 번 토글하면 정상으로 돌아옴...
	- 제대로 생성되지 않은 스프라이트(`SpriteCircle`에서 `__slots__` 활성화 시키면 발생)가 물리 모델을 망가뜨린 듯. 일단 버그는 해결됨.


# Dev Issues

## resizing, fullscreen
- 셰이더때문에 broken. 나중에 챙기자.
- 의도하는 바는, fov를 지키면서 리사이징 되는 것.


## 물리 컬리전 조정
- concave를 triangulate한 다음 convexise해서 적절한 컨벡스의 조합으로 변환하는 기능은 구현. 단일 counter-clockwise concave hull은 잘 된다.
- 블럭으로 쌓은 벽의 경우, 한 덩어리로 하지 않으면 프로젝타일이 살짝 들어가면서 접합부에서 튕겨나는 문제가 발생한다.
	- 물리 penetration을 방지하는 대책을 마련하거나,
	- penetration을 일으키지 않는 속도를 부여하거나(디자인 제약이 너무 커짐)
	- 컬리전을 재조정 해주는 기능을 구현하거나(아아 심플리곤이여...)
- 난이도 및 태스크의 성격을 고려할 때, 세 번째 방법으로 진행하는 것이 가장 낫다는 결론. (실수로 브랜치를 따지 않았네)
	- 이거 막상 하려니 엄청난 일이다. 심플리곤이 돈을 어떻게 번 건지 깨닫다.
- 기존의 convexise 함수를 바탕으로 triangle이 아니라 quad 이상을 컨벡스로 만들어주는 get_convex 구현. 맵 로딩 구현되면 가열차게 테스트 예정...
	- 버텍스 reduce 과정에서, 삼각형들에서 겹치는 선의 한 점만 남기고 삭제하는것이 기존의 convexise였기 때문에 연달아 붙어있는 박스들을 triangulate하고 convexise하면 점들이 남아돌아서 생기는 문제였음.
	- 아마 이후에 갈 길이 멀 것으로 예상(...)
- 일렬로 있지 않으면 문제 발생. 즉, 현재의 솔루션은 테스트 맵에서만 유효한 것으로.
- [[convex problems.excalidraw]]
- 결국 원하던 것을 했는데 완벽하지는 않다. tiled map의 그리기 순서를 믿고 간다.
	- 치명적인 것은, 닫힌 구조를 만들 수 없는 것. 닫힌 블럭을 만들게 되면 통짜 컬리전이 된다. 외각 벽은 이 수단을 통하지 않거나, 수작업 블로킹 볼륨을 넣어주거나, 꼼수(막힌 블럭 중 하나를 별도 처리)를 쓴다.
	- "...해치웠나!?"만 몇 번째.
	- 일단 이대로 업데이트.
- 중간에 구멍이 뚫리거나 3점 이상의 병합시 알고리즘 개선을 위해 다시 업데이트.
	- 닫힌 구조도 완벽하지는 않지만 지원한다. 레벨디자인시 컬리전상의 글리치(접합부 충돌 반응이 살짝 이상할 수 있지만 컬리전이 잘못 되는 것은 아님)를 감안할 것.
		- 분할 작업을 하거나 해당 구역을 못가게 만들어 놓으면 ㅇㅋ
		- 심지어, 맵 로딩시 드로잉 순서만 잘 지켜지면 글리치도 나타나지 않을 것으로 예상.

## 이동을 위한 힘 구하기
- [[python.pymunk|pymunk]] 기반에서는 위치 이동을 위해 `apply_force`가 필요.
	- 도달하기 원하는 max_speed, 가속도, 마찰력 하에서 적절한 힘의 스칼라값을 구할 수 있다.
	- 여기서 골치아파지는게 마찰력인데, 중력이 있고 damping이 0이면 바닥마찰력으로 계산하면 되지만, 

## pool 재활용
- GC를 하지 않고 재할당해서 쓰기.
	- 총알같은건 그렇게 하는것도 괜찮겠네.

## ECS entity component system
https://m.blog.naver.com/kiseop91/221855589754
https://github.com/benmoran56/esper
- 로직은 시스템에서 책임지고 엔티티와 컴포넌트는 데이터만 가진다. 데이터 직렬화가 필요.
- 생산성 대신 퍼포먼스를 위한 구조. 어떻게 잘 하면 생산성도 어느 정도 챙길 수 있을 것 같기는 한데...
- 어느 정도 현재 구현에 적용되어 있기는 하다. 컴포넌트에 processor가 녹아있는데, 이는 더 나은 생산성을 가져다준다. 비슷하지만 달라지는 기능들에 대응. (하지만 현 단계에서는 별로 필요하지 않음.)
- 적어도 물리 엔진의 코어와 렌더링은 이렇게 돌아가는 편이다.

## Garbage Collection
- GC 처리를 한꺼번에 해서 엄청난 랙이 발생하는 것이 확실해졌다.
- 이거 어떻게 안되나...
	- 수동으로 하는 방법 : `gc.collect()`

## ObjectLayer
- 어디까지나 sprite_list를 확장한 것이므로 이에 맞게 사용한다.
- 그려지는 순서 기준으로 나눠서 사용한다.
- 많이 써도(수백개는 아니고) 큰 부담은 없지만 관리가 골치아플 수 있으므로 신중하게 접근한다.
	- 게임디자인의 영역.
- 물리 공간 인스턴스를 두 개 이상 만들 경우, 메인과 서브로 구분한다.

## controller component
- 입력(조작) 혹은 명령(delegated 혹은 조건에 따른)에 의해 액터의 기능을 작동시키는 유닛.
	- 액터의 '의지' 역할을 한다. PC의 경우 조작을 반영, NPC의 경우 AI.
	- '리액션'은 컨트롤러가 책임지지 않는다. 조건으로는 받아들일 수 있다.
	- 매 틱마다 의지를 확인하고, 틱 단위의 명령을 내린다.
- 액터 컴포넌트로 제작할 경우, owner를 possess(own)하는 재미있는(?) 녀석.
	- 액터 tick에 포함된다.
- 플레이어 컨트롤러는 앱 혹은 ENV에서 특별 취급하여 on_inputs에서 delegation이 일어난다.
	- 입력 처리쪽은 별도로 연구할 주제.
- AI컨트롤러들의 틱을 돌릴 경우 순서대로 돌기 때문에 상호작용 과정에서 예기치 않은 결과가 나올 수 있다. 그룹AI 혹은 서로간의 거리 문제를 별도 취급해야 하는 이유.
	- 공간상의 계산이 필요한 경우 물리엔진의 힘을 빌린다.
- owner에게 명령을 내리는 것은 어떻게?
	- 일단 명령어셋의 스코프를 액터로 제한. 시스템 혹은 게임인스턴스에 명령을 내리는 것은 별도의 인터페이스를 둔다.
		- 예를 들어 플레이어컨트롤러에서 인벤토리창을 여는 것은 플레이어캐릭터의 역할을 벗어난다.
	- 컨트롤러는 명령을 내리는 '의지'이고, 명령을 수행하는 것은 다른 컴포넌트. 이동을 원하면 이동핸들러에 명령하고 이동핸들러가 틱마다 목표를 수행한다. 액션 명령을 내리면 액션핸들러가 마찬가지로 행동하고, 필요에 따라 무브락을 걸기도 한다. (복잡하구만)
		- 모든 명령은 껍데기, 즉 액터를 통한다. 액터가 모든 명령을 받을 준비가 되어있어야 한다.

## body component, physics
- 충돌 체크가 문제.
- 모든 액터는 아래와 같은 컬리전을 가진다.
	- 이동 충돌 체크용 컬리전
	- 피격 체크용 컬리전
	- 인터렉션 체크용 컬리전 (이건 특수하게 해야...?)
- 단순하게 비트맵 오버랩 체크가 낫지 않나?
- pymunk를 쓰려면 매 틱마다 apply force를 한다. f=ma이므로 결국 가속도를 주는 것.
- 지금까지의 방식; (물리'엔진'의 역할)
	- space, objects({sprite:physicsobject}), apply_\*, add, remove, step
		- sprite의 pymunk 멤버변수는 데이터 넣을 곳이 sprite 뿐이라 그런것.
	- 스프라이트 생성
	- 스프라이트 등록
		- 물리오브젝트(바디, 쉐잎)를 생성한다. 생성과 동시에 space에 add한다.
			- 바디와 쉐잎은 space 내에서 서로를 참조할 수 있다.
		- 스프라이트:물리오브젝트(바디, 쉐잎) dict에 밀어넣기
	- 물리엔진을 통해 대상 조작
		- 스프라이트를 통해 물리오브젝트(바디)에 조작을 가한다
	- 물리엔진 step
		- 각 body들이 움직이거나 회전하면서 shape에 따라 충돌을 일으킨다.
		- 만약 collision_type으로 등록된 컬리전 핸들러가 있으면 실행시킨다.
		- 동적 오브젝트들(static이 아닌)을 대상으로 싱크(물리바디의 정보로 스프라이트 좌표 각도 세팅)
			- 변화가 있는 경우 sprite.pymunk_moved를 실행시켜 별도의 업데이트를 해 준다.
	- 스프라이트 그리기
	- 충돌 체크
		- space에 직접 컬리전 타입을 넣어주고 핸들링 함수를 지정
- 물리엔진은 스프라이트와 물리바디들을 보유하고 이들에게 물리력을 가하며 스프라이트와 물리바디의 위치를 맞춰준다. 즉, 각 액터에 뭔가를 하는게 아니라 물리엔진을 통해서 하도록 되어있다. 충돌시 각 액터별로 뭔가를 해주고 싶으면 
- 나의 방식;
	- 액터 생성 -> 액터 바디 생성
		- 스프라이트를 지정해준다.
		- 물리body, shape 생성하여 지정.
	- 액터 스폰
		- 바디 스폰
			- 스프라이트는 필요시 그리기 리스트에 추가
			- 물리는 space에 add : 이 과정을 가능한 분리해 내야 편해짐
	- 액터를 직접 조작
		- space에 add된 물리객체에 직접 조작을 가한다.
	- 충돌 체크
- 액터를 생성하고 월드에 밀어넣는다.
	- 액터 생성시 body가 생성되는데, 그리기 위한 sprite와 충돌 체크를 위한 physics obj를 만든다. sprite는 렌더링을 위한 layer 리스트에 추가되고, physics obj는 물리공간에 추가되는데... space를 받는게 맞는지 아니면 물리엔진 인스턴스를 따로 가져가는게 맞는지.
	- 물리엔진 인스턴스는 space, 컬리전타입, 오브젝트(스프라이트, 물리바디)를 가진다.
		- 즉, 스프라이트만 밀어넣어 주면 알아서 space에 등록시킨다. 충돌 체크는 컬리전타입으로 알아서 세팅.
- 스태틱매시는 sprite로 생성하는데, 따로 오브젝트로 삼는게 맞을지?
- body 컴포넌트
	- 스프라이트, 물리오브젝트. 싱크를 물리엔진에서 하는게 아니라 바디컴포넌트에서 직접?
- 게임은 스프라이트로 이루어져 있다.
- 스태틱 오브젝트 : 스프라이트, 위치, 방향
	- 코드 효율만 보면 그냥 스프라이트로 생성해서 일괄 등록해주는게...
		- 절대 스태틱한 놈들은 그래도 되지만 조금이라도 변화의 가능성이 있으면 별도 클래스로 만들어줘야 한다.
- 다이나믹 오브젝트 : 스태틱 + 속도(가속도), 각속도(회전), 상태(HP등)

## tiled map
- 레벨 셋업
	- 월드 정보를 데이터 테이블에 넣고 테이블로 검사하는게 아니라...
	- 그냥 sprite list에 넣고 충돌로 모든 것을 체크한다.
	- `world.level.layer.draw()`
	- 레벨 : TiledMap 인스턴스
	- 렌더링할 레이어만 리스트로 관리?
- 월드에서 캐릭터도 관리? 이렇게 되면 단순히 월드가 아니라 게임 클래스가 되는게 낫지 않나.
- arcade와 함께 설치된 파서(pytiled-parser)가 tiled 버전을 못따라가서 최신버전으로 업데이트 하려니 약간 찜찜했는데, arcade 2.6.16이 나와줬다... ㄱㅅ...
	- ![[Pasted image 20220926134042.png]]


## camera handler
- 액터에 붙는다.
	- 액터틱에서 컴포넌트 실행.
- 카메라는 draw시 use하고 필요한 것들을 draw한다...


## clock, schedule
- 원래, 조금 더 정밀한 동시에 시간에 대한 제어권을 위해 clock 클래스를 만들었다. pygame에서는 내장 clock 객체가 선택 가능하기도 했고.
- arcade에서는 pyglet.clock이 기본으로 내장되어 강제로 돌아가기 때문에 커스텀 clock 클래스를 돌리는 것은 약간의 낭비일 뿐. (정밀도는 쓸만하지만 pygame보다 안좋다. 그냥 `time.perf_counter` 쓰는게 전부.)
- 게다가 완전한 타이머 기능은 아니지만 스케쥴 실행 기능이 있기는 하기 때문에 이쪽은 별도 구현 안하고 가져와서 쓰는걸로.
- `timer_get`같은 기능은 없기 때문에 내가 만든 clock과 같이 쓴다. delta_time도 그냥 pyglet거 쓰면 될 듯 한데...


## object structure
- 간단히, sprite 객체를 만들고 리스트에 넣은 다음, on_update에서 조작하고 on_draw에서 draw하면 끝.

## lightings / shadow
- 시야의 강제 제약
	- 시야각
	- 오브젝트에 의한 가림
- 빛의 양에 의한 제약
	- 거리에 따른 어테뉴에이션
	- 라이팅
- 빛의 양에 의한 제약을 먼저 계산하고 시야 제약을 오버라이딩 한다?