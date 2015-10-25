Vagrant.configure("2") do |config|
  2.times do |x|
    config.vm.define "machine#{x}" do |m|
        m.vm.box = "ubuntu/trusty64"
        m.vm.network "private_network", ip: "192.168.40.#{x}"
    end
  end
end
