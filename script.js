const contacts = {
  groom: { label: "신랑 김민준", phone: "01012345678" },
  bride: { label: "신부 이서연", phone: "01098765432" },
};

const weddingDate = new Date("2027-02-14T11:00:00+09:00");

const contactDialog = document.querySelector("#contactDialog");
const rsvpDialog = document.querySelector("#rsvpDialog");
const photoDialog = document.querySelector("#photoDialog");
const contactTitle = document.querySelector("#contactTitle");
const callLink = document.querySelector("#callLink");
const smsLink = document.querySelector("#smsLink");
const copyResult = document.querySelector("#copyResult");
const rsvpResult = document.querySelector("#rsvpResult");
const photoDialogImage = document.querySelector("#photoDialog img");

const setCountdown = () => {
  const diff = weddingDate.getTime() - Date.now();
  const safeDiff = Math.max(diff, 0);
  const totalSeconds = Math.floor(safeDiff / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  document.querySelector("#daysLeft").textContent = days;
  document.querySelector("#hoursLeft").textContent = hours;
  document.querySelector("#minutesLeft").textContent = minutes;
  document.querySelector("#secondsLeft").textContent = seconds;
  document.querySelector("#dateMessage").textContent = diff > 0 ? `${days + 1}일 남았습니다.` : "오늘입니다.";
};

document.querySelectorAll("[data-call]").forEach((button) => {
  button.addEventListener("click", () => {
    const contact = contacts[button.dataset.call] || contacts.groom;
    contactTitle.textContent = `${contact.label}에게 연락하기`;
    callLink.href = `tel:${contact.phone}`;
    smsLink.href = `sms:${contact.phone}`;
    contactDialog.showModal();
  });
});

document.querySelectorAll("[data-open='rsvp']").forEach((button) => {
  button.addEventListener("click", () => {
    rsvpResult.textContent = "";
    rsvpDialog.showModal();
  });
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      dialog.close();
    }
  });
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(button.dataset.copy);
      copyResult.textContent = "복사되었습니다.";
    } catch {
      copyResult.textContent = button.dataset.copy;
    }
  });
});

document.querySelectorAll("[data-photo]").forEach((button) => {
  button.addEventListener("click", () => {
    const image = button.querySelector("img");
    photoDialogImage.src = image.src;
    photoDialogImage.alt = image.alt || "확대된 웨딩 사진";
    photoDialog.showModal();
  });
});

document.querySelector("#rsvpForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  localStorage.setItem("wedding-rsvp", JSON.stringify(data));
  rsvpResult.textContent = `${data.name}님의 참석 의사가 저장되었습니다.`;
  event.currentTarget.reset();
});

document.querySelector("#soundButton").addEventListener("click", (event) => {
  const button = event.currentTarget;
  const isOn = button.classList.toggle("is-on");
  button.setAttribute("aria-pressed", String(isOn));
  button.setAttribute("aria-label", isOn ? "배경음악 끄기" : "배경음악 켜기");
});

document.querySelector("#albumButton").addEventListener("click", () => {
  document.querySelector("#albumNotice").textContent = "샘플 페이지에서는 업로드 기능이 비활성화되어 있습니다.";
});

document.querySelector("#shareButton").addEventListener("click", async () => {
  const shareData = {
    title: "민준 그리고 서연 결혼합니다.",
    text: "2027년 2월 14일 일요일 오전 11시, 비비드예식장",
    url: location.href,
  };

  if (navigator.share) {
    await navigator.share(shareData);
    return;
  }

  await navigator.clipboard.writeText(location.href);
  alert("청첩장 주소가 복사되었습니다.");
});

setCountdown();
setInterval(setCountdown, 1000);
