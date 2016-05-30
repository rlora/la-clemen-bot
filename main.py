# -*- coding: utf-8 -*-
#############################################################################
# Clementina: Bakery & Restaurant
# Time boxed POC: Telegram BOT
#
# This is part of the experiments and research conducted at Clementina to
# narrow down technology for The Box.
#
# POC constraint: 16hrs.
# Original release: 2016-05-12 
#############################################################################
import StringIO
import json
import logging
import random
import urllib
import urllib2
from datetime import datetime

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

#
# Telegram token assigned by the @botfather
#
TOKEN = 'YOUR_TELEGRAM_TOKEN'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'
#
# Google app engine base url
#
BASE_BOT_URL = 'https://YOUR_APP_IDENTIFIER_HERE.appspot.com/'
#
# Wit token gathered from wit.ai
#
WIT_TOKEN = 'YOUR_WIT_AI_TOKEN'
WIT_URL = 'https://api.wit.ai/converse'
WIT_API_VERSION = '20160330'
#
# Business phone number used in several examples
#
BUSINESS_PHONE_NUMBER = ''

###########################################################################################
# Random photos
###########################################################################################
RANDOM_PHOTOS = [
  {'url': 'assets/images/random/random-1.jpg', 'caption': u'Campesinos, baguettes, brioche. Prueba de laboratorio 2014.'},
  {'url': 'assets/images/random/random-2.jpg', 'caption': u'Pan de aceituna, perfecto para comerlo solo con aceite de oliva'},
  {'url': 'assets/images/random/random-3.jpg', 'caption': u'Albahaca del huerto! Uno de los ingredientes favoritos en Clementina'},
  {'url': 'assets/images/random/random-4.jpg', 'caption': u'Calentando el horno durante la mañana'},
  {'url': 'assets/images/random/random-5.jpg', 'caption': u'El huerto de Clementina y varias variedades de albahaca'},
  {'url': 'assets/images/random/random-6.jpg', 'caption': u'Este es Jack. Llegó perdido pero lo cuidamos y alimentamos hasta que encontró a su familia'},
  {'url': 'assets/images/random/random-7.jpg', 'caption': u'Lote de panes campesinos'},
  {'url': 'assets/images/random/random-8.jpg', 'caption': u'Café y pan tostado en mantequilla, que buena mañana!'},
  {'url': 'assets/images/random/random-9.jpg', 'caption': u'Un jueves con pesto Siciliano para llevar'},
  {'url': 'assets/images/random/random-10.jpg', 'caption': u'Lampara construida sobre la madera que atestiguó el paso de cientos de carretillas'},
  {'url': 'assets/images/random/random-11.jpg', 'caption': u'Cuando logramos asegurar un lote de leña de algarrobo danzamos de felicidad'},
  {'url': 'assets/images/random/random-12.jpg', 'caption': u'La calidez de la terraza y el patio trasero, esperando a nuestros clientes!'},
  {'url': 'assets/images/random/random-13.jpg', 'caption': u'El horno de Clementina es una obra de arte basada en diseños de Alan Scott'},
  {'url': 'assets/images/random/random-14.jpg', 'caption': u'Nada mejor que una tiza y pizarra para expresar el cariño por los chefs'},
  {'url': 'assets/images/random/random-15.jpg', 'caption': u'Cada hamburguesa es armada con mucho cariño y precisión.'},
  {'url': 'assets/images/random/random-16.jpg', 'caption': u'El pan del viernes se conserva muy bien hasta el Domingo. Para acompañar almuerzos especiales!'},
  {'url': 'assets/images/random/random-17.jpg', 'caption': u'Xavi evaluando un lote de pan. Abrobado!'},
  {'url': 'assets/images/random/random-18.jpg', 'caption': u'La hamburguesa San Francisco lista para juntarse con una copa de vino tinto. Una experiencia!'},
  {'url': 'assets/images/random/random-19.jpg', 'caption': u'Preparándonos para abrir, mostrador de pan listo, luces prendidas, lets go!'},
  {'url': 'assets/images/random/random-20.jpg', 'caption': u'Si te gustan los sabores fuertes, esta brusqueta de roquefort supera toda expectativa'},
  {'url': 'assets/images/random/random-21.jpg', 'caption': u'Pasta al pesto Siciliano, una verdadera locura.'}
]

class EnableStatus(ndb.Model):
  """Data store model that uses one property to track if conversation is enabled"""
  enabled = ndb.BooleanProperty(indexed=False, default=False)

def setEnabled(chat_id, is_enabled):
  """Changes the status of a conversation"""
  status = EnableStatus.get_or_insert(str(chat_id))
  status.enabled = is_enabled
  status.put()

def getEnabled(chat_id):
  """Gets the status of a conversation"""
  status = EnableStatus.get_by_id(str(chat_id))
  if status:
    return status.enabled
  return False

class MeHandler(webapp2.RequestHandler):
  """Get telegram bot information"""
  def get(self):
    urlfetch.set_default_fetch_deadline(60)
    self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

class GetUpdatesHandler(webapp2.RequestHandler):
  """Get telegram bot updates"""
  def get(self):
    urlfetch.set_default_fetch_deadline(60)
    self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

class SetWebhookHandler(webapp2.RequestHandler):
  """Subscribes webhook handler"""
  def get(self):
    urlfetch.set_default_fetch_deadline(60)
    url = self.request.get('url')
    if url:
      self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):
  """Main webhook handler entry point"""

  def post(self):
    """Handles requests from telegram bots"""

    ###########################################################################################
    # Read request and extract relevant info
    ###########################################################################################
    urlfetch.set_default_fetch_deadline(60)
    body = json.loads(self.request.body)
    logging.info('[webhook] request:')
    logging.info(body)
    self.response.write(json.dumps(body))

    update_id = body['update_id']
    message = body['message']
    message_id = message.get('message_id')
    customer = message.get('from').get('first_name')
    date = message.get('date')
    text = message.get('text') if 'text' in message else ''
    contact = message.get('contact')
    fr = message.get('from')
    chat = message['chat']
    chat_id = chat['id']

    ###########################################################################################
    # Helper methods to dispatch actions
    ###########################################################################################
    def sendContactCard():
      """Send phone number as a contact card"""
      resp = urllib2.urlopen(BASE_URL + 'sendContact', urllib.urlencode({
        'chat_id': str(chat_id),
        'phone_number': '4' + BUSINESS_PHONE_NUMBER,
        'first_name': 'Clementina',
        'last_name': 'Bakery & Restaurant',
        'reply_to_message_id': str(message_id)
      })).read()

    def sendContact():
      """Send a reply with contact information"""
      reply(
        u'Teléfono \U0000260e'
        u'\n' + BUSINESS_PHONE_NUMBER +
        u'\n\nFacebook \U0001f44d'
        u'\nhttps://www.facebook.com/clementina.restaurant/'
        u'\n\nTwitter \U0001f426'
        u'\nhttps://twitter.com/\_laclemen'
        u'\n\nWeb \U0001f578'
        u'\nhttp://clementina.com.bo/'
        u'\n\nO si prefieres solicita una /tarjeta con el número de teléfono \U0001f596'
      )

    def sendMenu():
      """Sends the current menu"""
      file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + 'assets/images/menu.png').read())
      reply(img=file.getvalue())

    def sendAddress():
      """Sends the location of the restaurant"""
      resp = urllib2.urlopen(BASE_URL + 'sendLocation', urllib.urlencode({
        'chat_id': str(chat_id),
        'latitude': -17.372102,
        'longitude': -66.155036,
        'reply_to_message_id': str(message_id)
      })).read()

    def sendRandomPhoto():
      """Sends a random photo"""
      choice = random.choice(RANDOM_PHOTOS)
      caption = choice.get('caption')
      image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + choice.get('url')).read())
      reply(img=image_file.getvalue(),  caption=caption)


    def forwardMessageToBot(msg=''):
      """Forwards a message to Wit.AI bot and tries to execute action"""
      if msg:
        request = urllib2.Request(WIT_URL + '?' + urllib.urlencode({
          'v': WIT_API_VERSION,
          'q': msg.encode('utf-8'),
          'session_id': chat_id
        }), {})
        request.add_header('Authorization', 'Bearer ' + WIT_TOKEN)
        request.add_header('Content-Type', 'application/json')
        resp = urllib2.urlopen(request)
        data = json.load(resp)
        logging.info(data)
        action = {}
        if (data and data['type'] == 'merge'):
          if ('entities' in data and 'intent' in data['entities']):
            action['intent'] = data['entities']['intent'][0]['value']
          if ('entities' in data and 'datetime' in data['entities']):
            action['datetime'] = datetime.strptime(data['entities']['datetime'][0]['value'][:19], '%Y-%m-%dT%H:%M:%S')
          if ('entities' in data and 'menu_item' in data['entities']):
            action['menu_item'] = data['entities']['menu_item'][0]['value']
          if ('entities' in data and 'bread_type' in data['entities']):
            action['bread_type'] = data['entities']['bread_type'][0]['value']
          if len(action) != 0:
            return handleBotResponse(action)

        return False
      else:
        return False

    def handleBotResponse(action):
      """Handles bot response when wit is able to gather entities"""
      intent = ''
      if not action or len(action) == 0:
        return False
      if 'intent' in action:
        intent = action['intent']
      if 'datetime' not in action:
        action['datetime'] = datetime.today()
      weekday = action['datetime'].isoweekday()
      bread_type = action.get('bread_type')
      menu_item = action.get('menu_item')

      ###########################################
      # Address
      ###########################################
      if intent == u'dirección':
        sendAddress()
        return True
      ###########################################
      # Telefono
      ###########################################
      elif intent == u'telefono':
        sendContact()
        return True
      ###########################################
      # Menu
      ###########################################
      elif intent == u'menu':
        sendMenu()
        return True
      ###########################################
      # Horarios
      ###########################################
      elif intent == u'horarios':
        reply(
          u'Los horarios de atención son:'
          u'\n\n*Venta de pan* \U0001f35e'
          u'\nMartes a Viernes a partir de las 18:00'
          u'\n\n*Restaurant* \U0001f35d'
          u'\nMartes a Sábado a partir de las 19.00'
          u'\n\nCocina recibe perdidos del menú hasta las *23:00*, y de esa hora en adelante solo bebidas y piqueos! \U0001f37b \U0001f37e \U0001f389'
        )
        return True
      ###########################################
      # Reclamo
      ###########################################
      elif intent == u'reclamo':
        image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + 'assets/images/sad-cat.jpg').read())
        reply(
          img=image_file.getvalue(),
          caption=u'Ohh no :( Tomamos los reclamos muy en serio. Por favor contáctate directamente con /tarjetaXavier o /tarjetaRolando'
        )
        return True
      ###########################################
      # Reserva
      ###########################################
      elif intent == u'reserva':
        reply(
          u'\U0001f440 oh my god \U0001f633\n\n'
          u'Las reservas no son lo mío. El pasado viernes reservé *cinco mesas* para *veinte* en lugar de *una para cinco* a las *20:00*.\n'
          u'\U0001f47b eso no les gustó a los chicos para nada.\n\n'
          u'Te pido te comuniques directamente al teléfono de /contacto\n\n'
          u'\U0001f648 \U0001f649 \U0001f64A \U0001f63b'
        )
        return True
      ###########################################
      # Recomendaciones
      ###########################################
      elif intent == u'recomendaciones':
        if menu_item:
          if menu_item == 'pastas':
            if weekday == 4:
              image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + RANDOM_PHOTOS[20]['url']).read())
              reply(
                img=image_file.getvalue(),
                caption=u'Los jueves son la oportunidad única para comer un buen pesto Siciliano!'
              )
            else:
              reply(u'Mi favorita esta temporada es la pasta al pesto! \U0001f44c Es un pesto maravilloso muy bien equilibrado y que combina tanto con la *pasta regular* como con la *libre de gluten*.')
          elif menu_item == 'sopas':
            reply(u'La sopa de cebolla! *no se diga más!* Esta sopa te transportará a Francia y te transmitirá calidez desde el primer bocado')
          elif menu_item == 'ensaladas':
            reply(u'Estamos realizando las últimas pruebas y pronto incluiremos ensaladas en el menu.')
          elif menu_item == 'hamburguesas':
            image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + RANDOM_PHOTOS[17]['url']).read())
            reply(
              img=image_file.getvalue(),
              caption=u'¿Que te parece una San Francisco? Inspirada en California: cebolla caramelizada, tomates deshidratados y una croqueta de Parmesano!'
            )
          elif menu_item == 'brusquetas':
            image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + RANDOM_PHOTOS[19]['url']).read())
            reply(
              img=image_file.getvalue(),
              caption=u'La brusqueta de roquefort!'
            )
        else:
          reply(
            u'Si aún no probaste las hamburguesas, te recomendamos empezar por ahí. \U0001f44c'
            u'\n\nPero las pastas y brusquetas son también muuuuuy buenas!'
          )
        return True
      ###########################################
      # Baking schedule
      ###########################################
      elif intent == 'agenda-pan':
        if bread_type:
          if bread_type == 'aceituna':
            image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + RANDOM_PHOTOS[1]['url']).read())
            reply(
              img=image_file.getvalue(),
              caption=u'Tenemos pan de aceituna los días Martes y Viernes. Te esperamos a partir de las 18:00!'
            )
          elif bread_type == 'semillas':
            reply(
              u'El poderoso pan de semillas está programado para los días Miércoles. \U0001f60b'
            )
          elif bread_type == 'campesino':
            reply(
              u'Pan *campesino* de Martes a Viernes. Pero los Viernes solamente '
              u'horneamos campesinos grandes. \U0000263a'
            )
          elif bread_type == 'integral':
            reply(
              u'El pan integral es la estrella de los Jueves \U0001f31f. El balance perfecto entre *salud y sabor*!'
            )
          elif bread_type == 'baguette':
            reply(
              u'Hacemos baguettes solo los días Viernes. Ven por ellos temprano! '
              u'Y recuerda abastecerte de pan para el fin de semana! \U0001f601'
            )
        elif weekday:
          if weekday == 1:
            image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + RANDOM_PHOTOS[12]['url']).read())
            reply(
              img=image_file.getvalue(),
              caption=u'Los Lunes no atendemos. Te esperamos desde el día Martes!'
            )
          elif weekday == 2:
            reply(
              u'Los Martes horneamos los siguientes panes:\n\n'
              u' - *Campesinos* _tipo boule, 875gr_\n'
              u' - *Campesinos* _tipo batard, 430gr_\n'
              u' - *Campesinos de aceituna* _tipo batard, 430g_\n'
              u'\n\nEmpezamos la semana con puro clásicos.'
              u'\nVen por tu pan *a partir de las 18:00*! \U0001f3c3'
            )
          elif weekday == 3:
            reply(
              u'Los Miércoles horneamos los siguientes panes:\n\n'
              u' - *Campesinos* _tipo boule, 875gr_\n'
              u' - *Campesinos* _tipo batard, 430gr_\n'
              u' - *Campesinos de semilla* _tipo batard, 430g_\n'
              u'\n\nEn los panes de semilla usualmente usamos lino, sésamo o girasol.'
              u'\nVenta de pan *a partir de las 18:00*! \U0001f596'
            )
          elif weekday == 4:
            reply(
              u'Los Jueves horneamos los siguientes panes:\n\n'
              u' - *Campesinos* _tipo boule, 875gr_\n'
              u' - *Campesinos* _tipo batard, 430gr_\n'
              u' - *Integrales* _tipo batard, 430g_\n'
              u'\n\nSi no probaste el pan integral deberías hacerlo! \U0001f44c'
              u'\nEs uno de nuestros favoritos. Te esperamos *a partir de las 18:00*!'
            )
          elif weekday == 5:
            reply(
              u'Los Viernes horneamos los siguientes panes:\n\n'
              u' - *Campesinos* _tipo boule, 875gr_\n'
              u' - *Campesino de aceituna* _tipo batard, 430g_\n'
              u' - *Pan francés* _tipo baguette, 430gr_'
              u'\n\nTe esperamos *a partir de las 18:00*! \U0001f64c'
            )
          elif weekday == 6:
            image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + RANDOM_PHOTOS[10]['url']).read())
            reply(
              img=image_file.getvalue(),
              caption=u'Los Sábados por lo general no horneamos. A veces queda algo de pan del Viernes, llama a consultar al \U0000260e ' + BUSINESS_PHONE_NUMBER + '.'
            )
          else:
            image_file = StringIO.StringIO(urllib.urlopen(BASE_BOT_URL + RANDOM_PHOTOS[15]['url']).read())
            reply(
              img=image_file.getvalue(),
              caption=u'Los Domingos no hacemos pan. Sin embargo el pan del viernes se conserva muy bien! (y acompaña perfectamente esos almuerzos especiales)'
            )
        return True
      ###########################################
      # At this point bot hasn't been able to
      # determine a valid answer path.
      ###########################################
      return False

    def reply(msg=None, img=None, caption=''):
      """Sends a basic reply to a telegram chat"""
      if msg:
        resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
          'chat_id': str(chat_id),
          'text': msg.encode('utf-8'),
          'disable_web_page_preview': 'true',
          'reply_to_message_id': str(message_id),
          'parse_mode': 'Markdown'
        })).read()
      elif img:
        resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
          ('chat_id', str(chat_id)),
          ('reply_to_message_id', str(message_id)),
          ('caption', caption.encode('utf-8'))
        ], [
          ('photo', 'image.jpg', img),
        ])
      else:
        logging.error('no msg or img specified')
        resp = None

    ###########################################################################################
    # Bot starts handling responses HERE. First menu actions then conversations.
    ###########################################################################################
    if text.startswith('/'):
      if text.startswith('/start'):
        reply(
          u'Hola ' + customer + '!'
          u'\n\nEstoy para ayudarte. \U0001f604 '
          u'\nSoy un *bot* en periodo de aprendizaje. Mi capacidad actual es muy '
          u'limitada.\n\nSin embargo me motiva muchisimo el poder aprender y ser de '
          u'más utilidad en el futuro! \U0001f917 \U0001f483'
          u'\n\n¿Qué necesitas?'
          u'\n\nTe aconsejo empezar solicitando la /ayuda'
        )
        setEnabled(chat_id, True)
      elif text.startswith('/ayuda'):
        reply(
          u'Para interactuar conmigo puedes hacer preguntas libres.\n\nPor ejemplo: '
          u'*hornean pan mañana?*, *me recomiendan una burger?* o *qué pasta está buena?*.'
          u'\n\nAdicionalmente respondo a los siguientes comandos:'
          u'\n\n/menu\nMenú vigente'
          u'\n\n/direccion\nDonde encontrarnos'
          u'\n\n/foto\nEscogida por mí para tí \U0001f618'
          u'\n\n/contacto\nTeléfono y otros datos'
          u'\n\n/ayuda\n\U0001f609'
        )
      elif text.startswith('/direccion'):
        sendAddress()
      elif text.startswith('/contacto'):
        sendContact()
      elif text.startswith('/tarjeta'):
        sendContactCard()
      elif text.startswith('/tarjetaXavier'):
        resp = urllib2.urlopen(BASE_URL + 'sendContact', urllib.urlencode({
          'chat_id': str(chat_id),
          'phone_number': '65369139',
          'first_name': 'Xavier',
          'last_name': 'Sarabia',
          'reply_to_message_id': str(message_id)
        })).read()
      elif text.startswith('/tarjetaRolando'):
        resp = urllib2.urlopen(BASE_URL + 'sendContact', urllib.urlencode({
          'chat_id': str(chat_id),
          'phone_number': '70716420',
          'first_name': 'Rolando',
          'last_name': 'Lora',
          'reply_to_message_id': str(message_id)
        })).read()
      elif text.startswith('/menu'):
        sendMenu()
      elif text.startswith('/foto'):
        sendRandomPhoto()
      elif text.startswith('/stop'):
        setEnabled(chat_id, False)
      else:
        reply(
          u'\U0001f633 \U0001f630 \U0001f630'
          u'\nLo siento \U0001f629 no reconozco ese comando.'
          u'\n\nQuieres intentar con la /ayuda? \U0001f917'
        )

    ###########################################################################################
    # Forward action to bot or come empty handed
    ###########################################################################################
    elif not forwardMessageToBot(text):
      reply(
        u'Todavía no puedo mantener una conversación \U0001f629, solamente intentar determinar tu intención y brindar ayuda en *cosas específicas*'
        u'\n\nPuedes intentar con la /ayuda? \U0001f917'
      )


app = webapp2.WSGIApplication([
  ('/me', MeHandler),
  ('/updates', GetUpdatesHandler),
  ('/set_webhook', SetWebhookHandler),
  ('/webhook', WebhookHandler),
], debug=True)
