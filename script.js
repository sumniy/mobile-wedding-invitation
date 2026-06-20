const contacts = {
  groom: { label: "신랑 김민준", phone: "01012345678" },
  bride: { label: "신부 이서연", phone: "01098765432" },
};

const contactDialog = document.querySelector("#contactDialog");
const accountDialog = document.querySelector("#accountDialog");
const contactTitle = document.querySelector("#contactTitle");
const callLink = document.querySelector("#callLink");
const smsLink = document.querySelector("#smsLink");
const copyResult = document.querySelector("#copyResult");
const messages = document.querySelector("#messages");

document.querySelectorAll("[data-call]").forEach((button) => {
  button.addEventListener("click", () => {
    const contact = contacts[button.dataset.call];
    contactTitle.textContent = `${contact.label}에게 연락하기`;
    callLink.href = `tel:${contact.phone}`;
    smsLink.href = `sms:${contact.phone}`;
    contactDialog.showModal();
  });
});

document.querySelectorAll("[data-open='account']").forEach((button) => {
  button.addEventListener("click", () => {
    copyResult.textContent = "";
    accountDialog.showModal();
  });
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    await navigator.clipboard.writeText(button.dataset.copy);
    copyResult.textContent = "계좌번호가 복사되었습니다.";
  });
});

document.querySelector("#rsvpForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  localStorage.setItem("wedding-rsvp", JSON.stringify(data));
  document.querySelector("#rsvpResult").textContent = `${data.name}님의 응답이 저장되었습니다.`;
  event.currentTarget.reset();
});

const renderMessages = () => {
  const saved = JSON.parse(localStorage.getItem("wedding-messages") || "[]");
  messages.innerHTML = "";
  saved.slice(-3).reverse().forEach((item) => {
    const li = document.createElement("li");
    const strong = document.createElement("strong");
    const p = document.createElement("p");
    strong.textContent = item.writer;
    p.textContent = item.message;
    li.append(strong, p);
    messages.append(li);
  });
};

document.querySelector("#messageForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  const saved = JSON.parse(localStorage.getItem("wedding-messages") || "[]");
  saved.push(data);
  localStorage.setItem("wedding-messages", JSON.stringify(saved));
  event.currentTarget.reset();
  renderMessages();
});

document.querySelector("#shareButton").addEventListener("click", async () => {
  const shareData = {
    title: "민준 그리고 서연의 모바일 청첩장",
    text: "2026년 10월 17일 토요일 오후 1시, 라움 아트센터",
    url: location.href,
  };

  if (navigator.share) {
    await navigator.share(shareData);
    return;
  }

  await navigator.clipboard.writeText(location.href);
  alert("청첩장 주소가 복사되었습니다.");
});

renderMessages();
